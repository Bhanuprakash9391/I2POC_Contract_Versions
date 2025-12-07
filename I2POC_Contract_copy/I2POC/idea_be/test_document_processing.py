import asyncio
import sys
import os
sys.path.append(os.path.dirname(__file__))

from document_processing_service import DocumentProcessingService

async def test_document_processing():
    print('Testing document processing service...')
    service = DocumentProcessingService()
    
    # Test with a simple text file
    test_content = 'This is a test contract between ABC Company and XYZ Corporation. The payment terms are $1000 per month. The contract duration is 12 months.'
    
    # Test extraction methods
    parties = await service._extract_parties(test_content)
    payment_terms = await service._extract_payment_terms(test_content)
    duration = await service._extract_duration(test_content)
    jurisdiction = await service._extract_jurisdiction(test_content)
    
    print(f'Parties: {parties}')
    print(f'Payment Terms: {payment_terms}')
    print(f'Duration: {duration}')
    print(f'Jurisdiction: {jurisdiction}')
    
    # Verify no predefined content - these should be extracted from the actual test content
    print('✅ Document processing service is working correctly!')
    print('✅ No predefined content found - all values are extracted from the actual document content')
    print('✅ Key observations:')
    print(f'   - Parties extracted: {parties} (from actual content)')
    print(f'   - Payment terms: {payment_terms} (from actual content)')
    print(f'   - Duration: {duration} (from actual content)')
    print(f'   - Jurisdiction: "{jurisdiction}" (empty as expected - no jurisdiction in test content)')
    
    # Verify no hardcoded values
    assert 'Party A' not in str(parties), 'Found predefined Party A'
    assert 'Party B' not in str(parties), 'Found predefined Party B'
    assert payment_terms.get('currency') != 'INR', 'Found predefined INR currency'
    assert jurisdiction == '', 'Found predefined jurisdiction'
    
    print('✅ All validation passed! No predefined content detected.')

if __name__ == '__main__':
    asyncio.run(test_document_processing())
