import React, { useState } from 'react';

const BASE_URL = '/apcontract';

const generateDraftsDocx = async (drafts, pocTitle) => {
  const { Document, Packer, Paragraph, TextRun } = await import("docx");

  const createFormattedSection = (title, content) => {
    const paragraphs = [];
    paragraphs.push(
      new Paragraph({
        children: [
          new TextRun({
            text: title,
            bold: true,
            color: "2F5496",
            size: 32,
            font: "Calibri",
          }),
        ],
        spacing: { after: 200 },
      })
    );

    const lines = content.split(/\n+/).filter(Boolean);
    for (const line of lines) {
      paragraphs.push(
        new Paragraph({
          children: [new TextRun({ text: line, size: 22, font: "Calibri" })],
          spacing: { after: 200, line: 276 },
        })
      );
    }
    return paragraphs;
  };

  const doc = new Document({
    sections: [
      {
        properties: {},
        children: Object.entries(drafts).flatMap(([title, content]) => createFormattedSection(title, content)),
      },
    ],
  });

  const blob = await Packer.toBlob(doc);
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement("a");
  const docName = pocTitle || "draft";
  link.href = url;
  link.download = `${docName}.docx`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};

const FileUploadSection = () => {
  const [contentFile, setContentFile] = useState(null);
  const [additionalInfo, setAdditionalInfo] = useState('');
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);
  const [error, setError] = useState('');
  const [sessionId, setSessionId] = useState('');
  const [missingFields, setMissingFields] = useState([]);
  const [userInputs, setUserInputs] = useState({});
  const [contractGenerated, setContractGenerated] = useState(false);
  const [finalContract, setFinalContract] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);

  const handleContentFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      const allowedTypes = ['.docx', '.doc', '.pdf', '.txt'];
      const fileExtension = file.name.toLowerCase().slice(file.name.lastIndexOf('.'));
      
      if (!allowedTypes.includes(fileExtension)) {
        setError(`Invalid file type. Allowed types: ${allowedTypes.join(', ')}`);
        setContentFile(null);
        return;
      }
      
      setContentFile(file);
      setError('');
    }
  };

  const handleGenerateContract = async () => {
    if (!contentFile && !additionalInfo.trim()) {
      setError('Please either upload a document or provide contract information in the text box');
      return;
    }

    setUploading(true);
    setError('');
    setUploadResult(null);
    setMissingFields([]);
    setUserInputs({});
    setContractGenerated(false);
    setFinalContract(null);
    setSessionId('');

    try {
      const formData = new FormData();
      
      // Add file if provided
      if (contentFile) {
        formData.append('file', contentFile);
      }
      
      // Add text information if provided
      if (additionalInfo.trim()) {
        formData.append('additional_info', additionalInfo.trim());
      }

      const response = await fetch(`${BASE_URL}/generate-contract-with-questions`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Contract generation failed');
      }

      const result = await response.json();
      setUploadResult(result);
      setSessionId(result.session_id);
      
      // Set missing fields directly from backend response
      if (result.missing_data && result.missing_data.length > 0) {
        setMissingFields(result.missing_data);
      }
      
      // Reset form
      setContentFile(null);
      setAdditionalInfo('');
      document.getElementById('content-file-input').value = '';

    } catch (err) {
      setError(err.message || 'An error occurred during contract generation');
      // Reset state on error
      resetProcess();
    } finally {
      setUploading(false);
    }
  };

  const handleInputChange = (field, value) => {
    setUserInputs(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleSubmitMissingData = async () => {
    if (!sessionId || missingFields.length === 0) return;

    setIsProcessing(true);
    try {
      // Create a new endpoint to submit all missing data at once
      const missingDataResponses = {};
      missingFields.forEach(field => {
        const answer = userInputs[field.field] || '';
        if (answer.trim()) {
          missingDataResponses[field.field] = answer;
        }
      });

      // Submit all missing data in one request
      const response = await fetch(`${BASE_URL}/submit-all-missing-data`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          session_id: sessionId,
          missing_data_responses: missingDataResponses
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to submit missing data');
      }

      const result = await response.json();
      
      if (result.type === 'end') {
        // Contract is complete
        setContractGenerated(true);
        console.log('Final contract received:', result.final_contract || result);
        setFinalContract(result.final_contract || result);
      } else {
        setError('Unexpected response from server');
      }
      
    } catch (err) {
      setError('Failed to submit missing data: ' + err.message);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleGenerateFinalContract = async () => {
    if (!sessionId) return;
    
    setIsProcessing(true);
    try {
      // Call the backend to generate the final contract
      const response = await fetch(`${BASE_URL}/get-next-question`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ session_id: sessionId }),
      });

      if (!response.ok) {
        throw new Error('Failed to generate final contract');
      }

      const result = await response.json();
      
      if (result.type === 'end') {
        // Contract is complete
        setContractGenerated(true);
        setFinalContract(result.final_contract || result);
      } else {
        // Should not happen if no missing fields, but handle gracefully
        setError('Unexpected response from server');
      }
    } catch (err) {
      setError('Failed to generate final contract: ' + err.message);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleSaveToCatalog = async () => {
    if (!finalContract) return;
    
    try {
      console.log('Final contract structure:', finalContract);
      
      // Extract contract title - check multiple possible locations
      const contractTitle = finalContract.title || finalContract.contract_title || 'Generated Contract';
      
      // Extract contract content from sections
      let contractDrafts = {};
      
      if (finalContract.sections && Array.isArray(finalContract.sections)) {
        // Use sections array to create drafts
        finalContract.sections.forEach(section => {
          if (section.heading && section.content) {
            contractDrafts[section.heading] = section.content;
          }
        });
      } else if (finalContract.drafts && typeof finalContract.drafts === 'object') {
        // Use existing drafts object
        contractDrafts = finalContract.drafts;
      }
      
      console.log('Extracted drafts:', contractDrafts);
      
      // If we have no content, show an error
      if (Object.keys(contractDrafts).length === 0) {
        alert('No contract content found to save. Please try generating the contract again.');
        return;
      }
      
      // Create the complete document from all drafts
      const completeDocument = Object.entries(contractDrafts)
        .map(([section, content]) => `## ${section}\n\n${content}`)
        .join('\n\n');
      
      console.log('Saving contract to catalog:', {
        title: contractTitle,
        sections_count: Object.keys(contractDrafts).length,
        completeDocument_length: completeDocument.length
      });
      
      // IMPORTANT FIX: Use the save-contract endpoint to update the existing contract
      // instead of creating a new one with /contracts endpoint
      const saveData = {
        session_id: sessionId, // Use the existing session ID
        contract: {
          title: contractTitle,
          drafts: contractDrafts,
          sections: finalContract.sections || []
        }
      };
      
      const response = await fetch(`${BASE_URL}/save-contract`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(saveData)
      });
      
      if (response.ok) {
        const result = await response.json();
        alert(`Contract "${contractTitle}" saved successfully! It will now appear in the Contract Catalog for review.`);
        console.log('Contract saved with session ID:', result.session_id);
      } else {
        const errorText = await response.text();
        console.error('Save failed:', errorText);
        alert('Failed to save contract. Please check if the backend server is running.');
      }
    } catch (error) {
      console.error('Error saving contract:', error);
      alert('Error saving contract. Please check if the backend server is running.');
    }
  };

  const handleDownloadContract = async () => {
    if (!finalContract) return;
    
    try {
      console.log('Final contract structure for download:', finalContract);
      
      // Extract contract title - check multiple possible locations
      const contractTitle = finalContract.title || finalContract.contract_title || 'Generated Contract';
      
      // Extract contract content from sections and format it properly
      let formattedContent = '';
      
      if (finalContract.sections && Array.isArray(finalContract.sections)) {
        // Use sections array to create formatted content
        finalContract.sections.forEach(section => {
          if (section.heading && section.content) {
            formattedContent += `## ${section.heading}\n\n${section.content}\n\n`;
          }
        });
      } else if (finalContract.drafts && typeof finalContract.drafts === 'object') {
        // Use existing drafts object to create formatted content
        Object.entries(finalContract.drafts).forEach(([section, content]) => {
          formattedContent += `## ${section}\n\n${content}\n\n`;
        });
      }
      
      console.log('Formatted content for download:', formattedContent);
      
      // If we have no content, show an error
      if (!formattedContent.trim()) {
        alert('No contract content found to download. Please try generating the contract again.');
        return;
      }
      
      // Create a proper filename based on contract type
      const filename = `${contractTitle.replace(/[^a-zA-Z0-9\s]/g, '').replace(/\s+/g, '_')}_Contract.docx`;
      
      // Use the simple generateDraftsDocx function that we know works
      let contractDrafts = {};
      
      if (finalContract.sections && Array.isArray(finalContract.sections)) {
        // Use sections array to create drafts
        finalContract.sections.forEach(section => {
          if (section.heading && section.content) {
            contractDrafts[section.heading] = section.content;
          }
        });
      } else if (finalContract.drafts && typeof finalContract.drafts === 'object') {
        // Use existing drafts object
        contractDrafts = finalContract.drafts;
      }
      
      await generateDraftsDocx(contractDrafts, contractTitle);
    } catch (error) {
      console.error('Error downloading contract:', error);
      alert('Error downloading contract. Please try again. Error details: ' + error.message);
    }
  };

  const resetProcess = () => {
    setSessionId('');
    setMissingFields([]);
    setUserInputs({});
    setContractGenerated(false);
    setFinalContract(null);
    setUploadResult(null);
  };

  return (
    <div className="max-w-4xl mx-auto p-6 bg-white rounded-lg shadow-md">
      <h2 className="text-2xl font-bold mb-6 text-gray-800">Contract Generation from Documents</h2>
      
      <div className="bg-green-50 border border-green-200 rounded-md p-4 mb-6">
        <h3 className="text-green-800 font-semibold mb-2">Upload Content & Generate Contract</h3>
        <p className="text-green-700 text-sm">
          Upload your contract content/document. The AI will analyze the content, identify missing information, 
          and generate a complete contract.
        </p>
      </div>

      {/* File Upload */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Upload Contract Content Document
        </label>
        <input
          id="content-file-input"
          type="file"
          accept=".docx,.doc,.pdf,.txt"
          onChange={handleContentFileChange}
          className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-green-50 file:text-green-700 hover:file:bg-green-100"
        />
        <p className="mt-1 text-sm text-gray-500">
          Supported formats: DOCX, DOC, PDF, TXT
        </p>
      </div>

      {/* Contract Information Input */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Contract Information (Alternative to File Upload)
        </label>
        <textarea
          value={additionalInfo}
          onChange={(e) => setAdditionalInfo(e.target.value)}
          placeholder="Type your contract information here. You can provide party names, contract duration, payment terms, obligations, or any other contract details. This can be used INSTEAD of uploading a document."
          className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-green-500 focus:border-green-500"
          rows="4"
        />
        <p className="mt-1 text-sm text-gray-500">
          Use this text box to provide contract information directly. You can use this INSTEAD of uploading a document, or in addition to it.
        </p>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4 mb-4">
          <p className="text-red-700 text-sm">{error}</p>
        </div>
      )}

      {/* Upload Result - Missing Fields Analysis */}
      {uploadResult && !contractGenerated && (
        <div className="bg-blue-50 border border-blue-200 rounded-md p-4 mb-4">
          <h3 className="text-blue-800 font-semibold mb-2">Document Analysis Complete</h3>
          <p className="text-blue-700 text-sm">{uploadResult.message}</p>
          
          {/* Available Information */}
          {uploadResult.extracted_info && (
            <div className="mt-3">
              <h4 className="text-blue-700 font-medium mb-2">✅ Information Found in Document:</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-sm">
                {uploadResult.extracted_info.parties && uploadResult.extracted_info.parties.length > 0 && (
                  <div className="text-green-600">• Parties: {uploadResult.extracted_info.parties.length} found</div>
                )}
                {uploadResult.extracted_info.key_terms > 0 && (
                  <div className="text-green-600">• Key Terms: {uploadResult.extracted_info.key_terms} found</div>
                )}
                {uploadResult.extracted_info.obligations > 0 && (
                  <div className="text-green-600">• Obligations: {uploadResult.extracted_info.obligations} found</div>
                )}
                {uploadResult.extracted_info.payment_terms && Object.keys(uploadResult.extracted_info.payment_terms).length > 0 && (
                  <div className="text-green-600">• Payment Terms: Available</div>
                )}
              </div>
            </div>
          )}
          
          {/* Missing Fields */}
          {missingFields.length > 0 && (
            <div className="mt-3">
              <h4 className="text-orange-700 font-medium mb-2">⚠️ Additional Information Needed ({missingFields.length} fields):</h4>
              <p className="text-orange-600 text-sm">
                Please provide the following additional information to complete the contract:
              </p>
              
              {/* Missing Fields Form */}
              <div className="mt-4 space-y-4">
                {missingFields.map((field, index) => (
                  <div key={index} className="border border-orange-200 rounded-md p-3 bg-orange-50">
                    <div className="flex justify-between items-start mb-2">
                      <label className="block text-sm font-medium text-orange-800">
                        {field.description}
                      </label>
                      <span className={`text-xs px-2 py-1 rounded-full ${
                        field.priority === 'high' ? 'bg-red-100 text-red-800' : 
                        field.priority === 'medium' ? 'bg-yellow-100 text-yellow-800' : 
                        'bg-blue-100 text-blue-800'
                      }`}>
                        {field.priority || 'medium'} priority
                      </span>
                    </div>
                    <textarea
                      value={userInputs[field.field] || ''}
                      onChange={(e) => handleInputChange(field.field, e.target.value)}
                      placeholder={`Enter ${field.field}...`}
                      className="w-full p-2 border border-orange-300 rounded-md focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
                      rows="2"
                    />
                    {field.reason && (
                      <p className="text-xs text-orange-600 mt-1">
                        <strong>Why this is needed:</strong> {field.reason}
                      </p>
                    )}
                  </div>
                ))}
                
                <div className="bg-blue-50 border border-blue-200 rounded-md p-3">
                  <p className="text-blue-700 text-sm">
                    <strong>Note:</strong> Only the most important missing fields are shown. If you have additional information, you can provide it in the text areas above.
                  </p>
                </div>
                
                <button
                  onClick={handleSubmitMissingData}
                  disabled={isProcessing}
                  className="w-full bg-orange-600 text-white py-2 px-4 rounded-md hover:bg-orange-700 focus:outline-none focus:ring-2 focus:ring-orange-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isProcessing ? 'Processing...' : 'Generate Final Contract'}
                </button>
              </div>
            </div>
          )}
          
          {/* No Missing Fields - Ready to Generate */}
          {uploadResult.missing_data_count === 0 && missingFields.length === 0 && (
            <div className="mt-3">
              <h4 className="text-green-700 font-medium mb-2">✅ All Information Complete!</h4>
              <p className="text-green-600 text-sm">
                Great! Your document contains all the necessary information. You can now generate the complete contract.
              </p>
              <button
                onClick={handleGenerateFinalContract}
                className="mt-3 bg-green-600 text-white py-2 px-4 rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2"
              >
                Generate Final Contract
              </button>
            </div>
          )}
          
          {uploadResult.session_id && (
            <p className="text-blue-700 text-sm mt-2">
              Session ID: {uploadResult.session_id}
            </p>
          )}
        </div>
      )}

      {/* Final Contract Success Message */}
      {contractGenerated && finalContract && (
        <div className="border border-green-200 rounded-md p-4">
          <h3 className="text-lg font-semibold mb-4 text-green-800">Contract Generated Successfully!</h3>
          
          <div className="bg-green-50 border border-green-200 rounded-md p-4 mb-4">
            <p className="text-green-700 text-sm mb-4">
              Your contract has been generated successfully. You can now save it to the catalog or download it as a Word document.
            </p>
            
            {/* Contract Summary */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
              {finalContract.title && (
                <div className="text-green-600">
                  <strong>Title:</strong> {finalContract.title}
                </div>
              )}
              {finalContract.drafts && (
                <div className="text-green-600">
                  <strong>Sections:</strong> {Object.keys(finalContract.drafts).length}
                </div>
              )}
              {finalContract.session_id && (
                <div className="text-green-600">
                  <strong>Session ID:</strong> {finalContract.session_id}
                </div>
              )}
            </div>
          </div>
          
          {/* Action Buttons */}
          <div className="flex space-x-4">
            <button
              onClick={handleSaveToCatalog}
              className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
            >
              Save to Catalog
            </button>
            <button
              onClick={handleDownloadContract}
              className="flex-1 bg-green-600 text-white py-2 px-4 rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2"
            >
              Download Contract
            </button>
          </div>
        </div>
      )}

      {/* Action Button */}
      {!sessionId && (
        <div className="pt-4">
          <button
            onClick={handleGenerateContract}
            disabled={uploading || (!contentFile && !additionalInfo.trim())}
            className="w-full bg-green-600 text-white py-2 px-4 rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {uploading ? 'Processing...' : 'Analyze Input & Identify Missing Data'}
          </button>
        </div>
      )}
    </div>
  );
};

export default FileUploadSection;
