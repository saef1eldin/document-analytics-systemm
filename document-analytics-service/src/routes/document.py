import os
import time
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from src.models.user import db
from src.models.document import Document, SearchLog
from src.utils.document_processor import DocumentProcessor

document_bp = Blueprint('document', __name__)
processor = DocumentProcessor()

@document_bp.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'message': 'Document Analytics Service is running',
        'endpoints': [
            '/api/health',
            '/api/statistics',
            '/api/debug/reset-db',
            '/api/search',
            '/api/documents',
            '/api/upload'
        ]
    }), 200

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'docx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def ensure_upload_folder():
    upload_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), UPLOAD_FOLDER)
    if not os.path.exists(upload_path):
        os.makedirs(upload_path)
    return upload_path

@document_bp.route('/upload', methods=['POST'])
def upload_document():
    """Upload and process a document"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'File type not allowed. Only PDF and DOCX files are supported.'}), 400
        
        # Save the file
        upload_path = ensure_upload_folder()
        filename = secure_filename(file.filename)
        file_path = os.path.join(upload_path, filename)
        file.save(file_path)
        
        # Process the document
        file_extension = filename.rsplit('.', 1)[1].lower()
        
        if file_extension == 'pdf':
            title = processor.extract_title_from_pdf(file_path)
            content_text = processor.extract_text_from_pdf(file_path)
            metadata = processor.extract_metadata_from_pdf(file_path)
        else:  # docx
            title = processor.extract_title_from_docx(file_path)
            content_text = processor.extract_text_from_docx(file_path)
            metadata = processor.extract_metadata_from_docx(file_path)
        
        # Classify the document
        classification, confidence = processor.classify_document(content_text)
        
        # Get file size
        file_size = os.path.getsize(file_path)
        
        # Create document record
        document = Document(
            title=title,
            filename=filename,
            file_path=file_path,
            file_size=file_size,
            content_text=content_text,
            classification=classification,
            classification_confidence=confidence,
            author=metadata.get('author'),
            creation_date=metadata.get('creation_date'),
            last_modified=metadata.get('last_modified')
        )
        
        db.session.add(document)
        db.session.commit()
        
        return jsonify({
            'message': 'Document uploaded and processed successfully',
            'document': document.to_dict()
        }), 201
        
    except Exception as e:
        return jsonify({'error': f'Error processing document: {str(e)}'}), 500

@document_bp.route('/documents', methods=['GET'])
def get_documents():
    """Get all documents with optional sorting"""
    try:
        sort_by = request.args.get('sort_by', 'upload_date')
        sort_order = request.args.get('sort_order', 'desc')
        
        # Measure sorting time
        start_time = time.time()
        
        query = Document.query
        
        if sort_by == 'title':
            if sort_order == 'asc':
                query = query.order_by(Document.title.asc())
            else:
                query = query.order_by(Document.title.desc())
        elif sort_by == 'upload_date':
            if sort_order == 'asc':
                query = query.order_by(Document.upload_date.asc())
            else:
                query = query.order_by(Document.upload_date.desc())
        elif sort_by == 'file_size':
            if sort_order == 'asc':
                query = query.order_by(Document.file_size.asc())
            else:
                query = query.order_by(Document.file_size.desc())
        
        documents = query.all()
        sort_time = time.time() - start_time
        
        return jsonify({
            'documents': [doc.to_dict() for doc in documents],
            'sort_time': sort_time,
            'total_count': len(documents)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error retrieving documents: {str(e)}'}), 500

@document_bp.route('/search', methods=['POST'])
def search_documents():
    """Search documents by keywords"""
    try:
        data = request.get_json()
        keywords = data.get('keywords', '').strip()
        
        if not keywords:
            return jsonify({'error': 'Keywords are required'}), 400
        
        # Measure search time
        start_time = time.time()
        
        # Get all documents
        all_documents = Document.query.all()
        documents_data = [doc.to_dict() for doc in all_documents]
        
        # Search and highlight
        matching_documents = processor.search_documents(documents_data, keywords)
        
        search_time = time.time() - start_time
        
        # Log the search
        search_log = SearchLog(
            query=keywords,
            results_count=len(matching_documents),
            search_time=search_time
        )
        db.session.add(search_log)
        db.session.commit()
        
        return jsonify({
            'documents': matching_documents,
            'search_time': search_time,
            'results_count': len(matching_documents),
            'total_documents': len(all_documents),
            'query': keywords,
            'keywords_searched': keywords.split()
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error searching documents: {str(e)}'}), 500

@document_bp.route('/classify', methods=['POST'])
def classify_documents():
    """Classify all documents or reclassify existing ones"""
    try:
        start_time = time.time()
        
        documents = Document.query.all()
        classified_count = 0
        
        for document in documents:
            if document.content_text:
                classification, confidence = processor.classify_document(document.content_text)
                document.classification = classification
                document.classification_confidence = confidence
                classified_count += 1
        
        db.session.commit()
        classification_time = time.time() - start_time
        
        return jsonify({
            'message': f'Successfully classified {classified_count} documents',
            'classification_time': classification_time,
            'classified_count': classified_count
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error classifying documents: {str(e)}'}), 500

@document_bp.route('/statistics', methods=['GET'])
def get_statistics():
    """Get system statistics"""
    try:
        # Document statistics
        total_documents = Document.query.count()
        total_size = db.session.query(db.func.sum(Document.file_size)).scalar() or 0

        # Classification statistics
        classification_stats = db.session.query(
            Document.classification,
            db.func.count(Document.id)
        ).filter(Document.classification.isnot(None)).group_by(Document.classification).all()

        # Convert classification stats to dictionary
        classification_distribution = {}
        for category, count in classification_stats:
            if category:  # Only include non-null categories
                classification_distribution[category] = count

        # Search statistics - Fixed the query issue
        try:
            # Check if SearchLog table exists and has data
            total_searches = SearchLog.query.count()
            if total_searches > 0:
                recent_searches = SearchLog.query.order_by(SearchLog.timestamp.desc()).limit(10).all()
                avg_search_time = db.session.query(db.func.avg(SearchLog.search_time)).scalar() or 0
            else:
                recent_searches = []
                avg_search_time = 0
        except Exception as search_error:
            print(f"Search statistics error: {str(search_error)}")
            recent_searches = []
            avg_search_time = 0
            total_searches = 0

        return jsonify({
            'total_documents': total_documents,
            'total_size_bytes': int(total_size),
            'total_size_mb': round(total_size / (1024 * 1024), 2) if total_size > 0 else 0,
            'classification_distribution': classification_distribution,
            'recent_searches': [search.to_dict() for search in recent_searches] if recent_searches else [],
            'average_search_time': round(float(avg_search_time), 4) if avg_search_time else 0,
            'total_searches': total_searches
        }), 200

    except Exception as e:
        print(f"Statistics error: {str(e)}")  # للتشخيص
        return jsonify({'error': f'Error retrieving statistics: {str(e)}'}), 500

@document_bp.route('/document/<int:document_id>', methods=['GET'])
def get_document(document_id):
    """Get a specific document by ID"""
    try:
        document = Document.query.get_or_404(document_id)
        return jsonify({'document': document.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': f'Error retrieving document: {str(e)}'}), 500

@document_bp.route('/document/<int:document_id>', methods=['DELETE'])
def delete_document(document_id):
    """Delete a specific document"""
    try:
        document = Document.query.get_or_404(document_id)
        
        # Delete the file from filesystem
        if os.path.exists(document.file_path):
            os.remove(document.file_path)
        
        # Delete from database
        db.session.delete(document)
        db.session.commit()
        
        return jsonify({'message': 'Document deleted successfully'}), 200

    except Exception as e:
        return jsonify({'error': f'Error deleting document: {str(e)}'}), 500

@document_bp.route('/debug/reset-db', methods=['POST'])
def reset_database():
    """Reset database and create sample data for testing"""
    try:
        # Clear existing data
        SearchLog.query.delete()
        Document.query.delete()
        db.session.commit()

        # Create sample documents for testing
        sample_docs = [
            {
                'title': 'Sample Business Report',
                'filename': 'business_report.pdf',
                'file_path': '/fake/path/business_report.pdf',
                'file_size': 1024000,
                'content_text': 'This is a comprehensive business report about market analysis and revenue growth. The company has shown significant improvement in quarterly results. Our financial performance exceeded expectations this year. The market research indicates strong customer satisfaction and brand loyalty. We recommend continued investment in digital transformation initiatives.',
                'classification': 'Business',
                'classification_confidence': 0.85
            },
            {
                'title': 'Technical Documentation',
                'filename': 'tech_doc.pdf',
                'file_path': '/fake/path/tech_doc.pdf',
                'file_size': 2048000,
                'content_text': 'Technical documentation for software development and system architecture. This document covers programming best practices, code review guidelines, and deployment strategies. The development team should follow these established protocols for quality assurance. Database optimization techniques are discussed in detail. Security considerations include authentication and authorization mechanisms.',
                'classification': 'Technical',
                'classification_confidence': 0.92
            },
            {
                'title': 'Academic Research Paper',
                'filename': 'research.pdf',
                'file_path': '/fake/path/research.pdf',
                'file_size': 1536000,
                'content_text': 'Academic research paper on machine learning algorithms and artificial intelligence applications. The study analyzes various approaches to data classification and pattern recognition. Experimental results demonstrate improved accuracy in predictive modeling. The research methodology includes statistical analysis and cross-validation techniques. Future work will explore deep learning architectures.',
                'classification': 'Academic',
                'classification_confidence': 0.78
            }
        ]

        for doc_data in sample_docs:
            doc = Document(**doc_data)
            db.session.add(doc)

        # Create sample search logs
        sample_searches = [
            {'query': 'business', 'results_count': 1, 'search_time': 0.045},
            {'query': 'technical', 'results_count': 1, 'search_time': 0.032},
            {'query': 'research', 'results_count': 1, 'search_time': 0.028},
            {'query': 'data', 'results_count': 2, 'search_time': 0.051}
        ]

        for search_data in sample_searches:
            search_log = SearchLog(**search_data)
            db.session.add(search_log)

        db.session.commit()

        return jsonify({
            'message': 'Database reset successfully',
            'sample_documents_created': len(sample_docs),
            'sample_searches_created': len(sample_searches)
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error resetting database: {str(e)}'}), 500

@document_bp.route('/debug/test-search', methods=['POST'])
def test_search():
    """Test search functionality with detailed debugging"""
    try:
        data = request.get_json()
        keywords = data.get('keywords', '').strip()

        if not keywords:
            return jsonify({'error': 'Keywords are required'}), 400

        # Get all documents
        all_documents = Document.query.all()
        documents_data = [doc.to_dict() for doc in all_documents]

        # Debug information
        debug_info = {
            'total_documents_in_db': len(all_documents),
            'keywords_to_search': keywords,
            'documents_content_preview': []
        }

        # Add detailed preview of document content for debugging
        for doc in documents_data:
            content_text = doc.get('content_text', '')
            debug_info['documents_content_preview'].append({
                'id': doc.get('id'),
                'title': doc.get('title', ''),
                'filename': doc.get('filename', ''),
                'content_length': len(content_text),
                'content_preview': content_text[:500] + '...' if len(content_text) > 500 else content_text,
                'content_contains_keyword': keywords.lower() in content_text.lower() if content_text else False,
                'classification': doc.get('classification', 'None')
            })

        # Perform search
        matching_documents = processor.search_documents(documents_data, keywords)

        return jsonify({
            'debug_info': debug_info,
            'search_results': matching_documents,
            'results_count': len(matching_documents),
            'query': keywords
        }), 200

    except Exception as e:
        return jsonify({'error': f'Error in test search: {str(e)}'}), 500

@document_bp.route('/debug/document-content/<int:document_id>', methods=['GET'])
def get_document_content_debug(document_id):
    """Get full content of a document for debugging"""
    try:
        document = Document.query.get_or_404(document_id)
        doc_dict = document.to_dict()

        return jsonify({
            'document_id': document_id,
            'title': doc_dict.get('title', ''),
            'filename': doc_dict.get('filename', ''),
            'content_length': len(doc_dict.get('content_text', '')),
            'full_content': doc_dict.get('content_text', ''),
            'classification': doc_dict.get('classification', 'None'),
            'file_size': doc_dict.get('file_size', 0)
        }), 200

    except Exception as e:
        return jsonify({'error': f'Error retrieving document content: {str(e)}'}), 500

@document_bp.route('/debug/reprocess-documents', methods=['POST'])
def reprocess_documents():
    """Reprocess all documents to extract text content again"""
    try:
        documents = Document.query.all()
        processed_count = 0
        errors = []

        for document in documents:
            try:
                if os.path.exists(document.file_path):
                    # Re-extract text content
                    if document.filename.lower().endswith('.pdf'):
                        new_content = processor.extract_text_from_pdf(document.file_path)
                        new_title = processor.extract_title_from_pdf(document.file_path)
                    elif document.filename.lower().endswith('.docx'):
                        new_content = processor.extract_text_from_docx(document.file_path)
                        new_title = processor.extract_title_from_docx(document.file_path)
                    else:
                        continue

                    # Update document with new content
                    document.content_text = new_content
                    document.title = new_title

                    # Re-classify if content changed
                    if new_content:
                        classification, confidence = processor.classify_document(new_content)
                        document.classification = classification
                        document.classification_confidence = confidence

                    processed_count += 1
                    print(f"Reprocessed document: {document.filename}, Content length: {len(new_content)}")

                else:
                    errors.append(f"File not found: {document.file_path}")

            except Exception as e:
                errors.append(f"Error processing {document.filename}: {str(e)}")

        db.session.commit()

        return jsonify({
            'message': f'Successfully reprocessed {processed_count} documents',
            'processed_count': processed_count,
            'total_documents': len(documents),
            'errors': errors
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error reprocessing documents: {str(e)}'}), 500

@document_bp.route('/debug/test-highlight', methods=['POST'])
def test_highlight():
    """Test text highlighting functionality"""
    try:
        data = request.get_json()
        text = data.get('text', '')
        terms = data.get('terms', [])

        if not text or not terms:
            return jsonify({'error': 'Both text and terms are required'}), 400

        # Test highlighting
        highlighted = processor.highlight_text(text, terms)

        return jsonify({
            'original_text': text,
            'search_terms': terms,
            'highlighted_text': highlighted,
            'contains_mark_tags': '<mark>' in highlighted,
            'text_length': len(text),
            'highlighted_length': len(highlighted)
        }), 200

    except Exception as e:
        return jsonify({'error': f'Error testing highlight: {str(e)}'}), 500

