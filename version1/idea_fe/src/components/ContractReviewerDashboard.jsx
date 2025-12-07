import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';


const ContractReviewerDashboard = () => {
  const [contracts, setContracts] = useState([]);
  const [selectedContract, setSelectedContract] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('ai-reviewer');
  const [selectedAiContract, setSelectedAiContract] = useState(null);

  // Fetch real data from API - only show contracts that need review (submitted status)
  useEffect(() => {
    const fetchContracts = async () => {
      try {
        const response = await fetch('/apcontract/contracts');
        if (response.ok) {
          const data = await response.json();
          // Transform API data to match component format
          const contractMap = new Map();
          data.ideas.forEach(contract => {
            // Use session_id as unique key to prevent duplicates
            // Only include contracts that are submitted (need review) and not already approved/rejected
            if (!contractMap.has(contract.session_id) && 
                (contract.status === 'submitted' || contract.status === 'completed' || contract.status === 'in_progress')) {
              // Generate full draft text from all_drafts
              const generateFullDraft = () => {
                console.log('=== DEBUG: Processing contract ===');
                console.log('Contract title:', contract.title);
                console.log('Contract session_id:', contract.session_id);
                console.log('Contract status:', contract.status);
                console.log('All drafts:', contract.all_drafts);
                console.log('Drafts:', contract.drafts);
                console.log('Contract content:', contract.idea);
                console.log('Rephrased contract:', contract.rephrased_idea);
                console.log('Original contract:', contract.original_idea);
                
                // Get all drafts from the contract - prioritize drafts field from database
                const allDrafts = contract.drafts || contract.all_drafts || {};
                console.log('Using drafts object:', allDrafts);
                console.log('Drafts keys:', Object.keys(allDrafts));
                
                if (Object.keys(allDrafts).length > 0) {
                  console.log('Found drafts sections:', Object.keys(allDrafts));
                  // Combine all section drafts into a complete document
                  let fullDraft = '';
                  Object.entries(allDrafts).forEach(([section, draft]) => {
                    console.log(`Section: ${section}, Draft content:`, draft);
                    console.log(`Section ${section} has content:`, draft && draft.trim() && draft !== 'No draft content available');
                    if (draft && draft.trim() && draft !== 'No draft content available') {
                      fullDraft += `## ${section}\n\n${draft}\n\n`;
                    }
                  });
                  
                  if (fullDraft.trim()) {
                    console.log('✅ SUCCESS: Returning full draft content');
                    return fullDraft;
                  } else {
                    console.log('⚠️ WARNING: Drafts exist but no valid content found - using fallback');
                    return `## Contract Summary\n\nThis contract has draft sections but the content appears to be empty or placeholder text.\n\n**Available Sections:** ${Object.keys(allDrafts).join(', ')}\n\nPlease check if the Q&A process was completed properly.`;
                  }
                } else {
                  console.log('⚠️ WARNING: No drafts found in contract object - using fallback content');
                  // Try to use other available content
                  if (contract.idea && contract.idea.trim() && contract.idea !== 'No draft content available') {
                    console.log('✅ Using contract content as fallback');
                    return contract.idea;
                  } else if (contract.rephrased_idea && contract.rephrased_idea.trim()) {
                    console.log('✅ Using rephrased contract as fallback');
                    return contract.rephrased_idea;
                  } else if (contract.original_idea && contract.original_idea.trim() && contract.original_idea !== 'No draft content available') {
                    console.log('✅ Using original contract as fallback');
                    return contract.original_idea;
                  } else {
                    console.log('⚠️ No content available - using default message');
                    return 'Contract document content will be available after completing the Q&A process. This contract is still in progress or the draft content has not been generated yet.';
                  }
                }
              };
              
              let fullDraft;
              try {
                fullDraft = generateFullDraft();
              } catch (error) {
                console.error('Error generating draft:', error);
                fullDraft = `Error generating draft content: ${error.message}\n\nPlease check the browser console for detailed debug information.`;
              }
              
              contractMap.set(contract.session_id, {
                id: contract.session_id,
                title: contract.title || 'Untitled Contract',
                department: contract.metadata?.department || 'Legal',
                status: (contract.status === 'completed' || contract.status === 'in_progress') ? 'submitted' : contract.status || 'submitted',
                submittedBy: contract.metadata?.submitted_by || 'Anonymous',
                submittedDate: contract.metadata?.created_at ? new Date(contract.metadata.created_at).toISOString().split('T')[0] : 'Unknown',
                evaluationScore: contract.metadata?.evaluation_score || contract.evaluation_score || null,
                reviewerFeedback: contract.metadata?.reviewer_feedback || contract.reviewer_feedback || null,
                aiScore: contract.ai_score || null,
                aiFeedback: contract.ai_feedback || null,
                aiStrengths: contract.ai_strengths || [],
                aiImprovements: contract.ai_improvements || [],
                aiRiskLevel: contract.ai_risk_level || 'Medium',
                summary: fullDraft
              });
            }
          });
          const transformedContracts = Array.from(contractMap.values());
          setContracts(transformedContracts);
        } else {
          console.error('Failed to fetch contracts:', response.status);
          setContracts([]);
        }
      } catch (error) {
        console.error('Error fetching contracts:', error);
        setContracts([]);
      } finally {
        setLoading(false);
      }
    };

    fetchContracts();
  }, []);


  const handleEvaluateContract = async (contractId, score, feedback, status) => {
    try {
      // Call backend API to update the contract status and score
      const response = await fetch('/apcontract/update-contract-status', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: contractId,
          status: status,
          evaluation_score: score,
          reviewer_feedback: feedback
        })
      });

      if (response.ok) {
        // Update local state only if backend update is successful
        setContracts(prevContracts => 
          prevContracts.map(contract => 
            contract.id === contractId 
              ? { ...contract, evaluationScore: score, status: status, reviewerFeedback: feedback }
              : contract
          )
        );
        setSelectedContract(null);
        alert('Contract evaluation saved successfully!');
      } else {
        alert('Failed to save evaluation. Please try again.');
      }
    } catch (error) {
      console.error('Error updating contract status:', error);
      alert('Error saving evaluation. Please try again.');
    }
  };


  const getStatusColor = (status) => {
    switch (status) {
      case 'submitted': return 'bg-yellow-100 text-yellow-800';
      case 'approved': return 'bg-green-100 text-green-800';
      case 'rejected': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getScoreColor = (score) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getRiskColor = (riskLevel) => {
    switch (riskLevel) {
      case 'Low': return 'text-green-600 bg-green-100';
      case 'Medium': return 'text-yellow-600 bg-yellow-100';
      case 'High': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading contracts...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Fixed Stats and Tabs Section */}
      <div className="bg-white border-b sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* Stats Overview - Only showing contracts that need review */}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-5 py-4">
            <div className="bg-gray-50 overflow-hidden shadow rounded-lg">
              <div className="px-4 py-3">
                <dt className="text-sm font-medium text-gray-500 truncate">Contracts for Review</dt>
                <dd className="mt-1 text-2xl font-semibold text-gray-900">{contracts.length}</dd>
              </div>
            </div>
            <div className="bg-gray-50 overflow-hidden shadow rounded-lg">
              <div className="px-4 py-3">
                <dt className="text-sm font-medium text-gray-500 truncate">Pending Review</dt>
                <dd className="mt-1 text-2xl font-semibold text-yellow-600">
                  {contracts.filter(c => c.status === 'submitted').length}
                </dd>
              </div>
            </div>
            <div className="bg-gray-50 overflow-hidden shadow rounded-lg">
              <div className="px-4 py-3">
                <dt className="text-sm font-medium text-gray-500 truncate">Approved</dt>
                <dd className="mt-1 text-2xl font-semibold text-green-600">
                  {contracts.filter(c => c.status === 'approved').length}
                </dd>
              </div>
            </div>
            <div className="bg-gray-50 overflow-hidden shadow rounded-lg">
              <div className="px-4 py-3">
                <dt className="text-sm font-medium text-gray-500 truncate">Rejected</dt>
                <dd className="mt-1 text-2xl font-semibold text-red-600">
                  {contracts.filter(c => c.status === 'rejected').length}
                </dd>
              </div>
            </div>
            <div className="bg-gray-50 overflow-hidden shadow rounded-lg">
              <div className="px-4 py-3">
                <dt className="text-sm font-medium text-gray-500 truncate">Avg. Score</dt>
                <dd className="mt-1 text-2xl font-semibold text-green-600">
                  {Math.round(contracts.filter(c => c.evaluationScore).reduce((acc, c) => acc + c.evaluationScore, 0) / 
                   (contracts.filter(c => c.evaluationScore).length || 1))}
                </dd>
              </div>
            </div>
          </div>

          {/* Tab Navigation */}
          <div className="border-t border-gray-200">
            <nav className="-mb-px flex space-x-8">
              <button
                onClick={() => setActiveTab('ai-reviewer')}
                className={`whitespace-nowrap py-3 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'ai-reviewer'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                AI Legal Reviewer
              </button>
              <button
                onClick={() => setActiveTab('contract-review')}
                className={`whitespace-nowrap py-3 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'contract-review'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Human Contract Review
              </button>
            </nav>
          </div>
        </div>
      </div>

      {/* Scrollable Content Area */}
      <div className="max-w-7xl mx-auto py-4 sm:px-6 lg:px-8">
        <div className="px-4 sm:px-0">

          {/* Tab Content */}
          {activeTab === 'ai-reviewer' && (
            <div className="space-y-6">
              {/* AI Reviewer Header */}
              <div className="bg-white p-6 rounded-lg shadow">
                <div className="mb-4">
                  <h3 className="text-lg font-semibold text-gray-900">AI Legal Reviewer</h3>
                  <p className="text-sm text-gray-600">Contracts are automatically scored by AI when submitted</p>
                </div>
                <div className="text-sm text-gray-600">
                  <p>All contracts are automatically evaluated by AI as soon as they are uploaded. Click on any contract to view detailed AI legal feedback, scores, and risk assessments.</p>
                </div>
              </div>

              {/* AI Scored Contracts - Simplified List */}
              <div className="bg-white shadow overflow-hidden sm:rounded-lg">
                <div className="px-4 py-5 sm:px-6 border-b border-gray-200">
                  <h3 className="text-lg leading-6 font-medium text-gray-900">AI-Scored Contracts</h3>
                  <p className="mt-1 max-w-2xl text-sm text-gray-500">Click on any contract to view detailed AI legal feedback</p>
                </div>
                <div className="divide-y divide-gray-200">
                  {contracts.map((contract) => (
                    <motion.div
                      key={contract.id}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.3 }}
                      className="px-4 py-4 hover:bg-gray-50 cursor-pointer"
                      onClick={() => setSelectedAiContract(contract)}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <div className="flex items-center justify-between">
                            <p className="text-sm font-medium text-indigo-600 truncate">
                              {contract.title}
                            </p>
                            <div className="ml-2 flex-shrink-0 flex gap-2">
                              {contract.aiScore !== null ? (
                                <>
                                  <span className={`px-3 py-1 rounded-full text-sm font-medium ${getScoreColor(contract.aiScore)} bg-opacity-20`}>
                                    AI Score: {contract.aiScore}/100
                                  </span>
                                  <span className={`px-3 py-1 rounded-full text-sm font-medium ${getRiskColor(contract.aiRiskLevel)}`}>
                                    Risk: {contract.aiRiskLevel}
                                  </span>
                                </>
                              ) : (
                                <span className="px-3 py-1 rounded-full text-sm font-medium bg-yellow-100 text-yellow-800">
                                  AI Score: Pending
                                </span>
                              )}
                            </div>
                          </div>
                          <div className="mt-2 flex flex-wrap gap-4">
                            <div className="flex items-center text-sm text-gray-500">
                              <strong>Department:</strong> {contract.department}
                            </div>
                            <div className="flex items-center text-sm text-gray-500">
                              <strong>Submitted by:</strong> {contract.submittedBy}
                            </div>
                            <div className="flex items-center text-sm text-gray-500">
                              <strong>Date:</strong> {contract.submittedDate}
                            </div>
                          </div>
                        </div>
                        <div className="ml-5 flex-shrink-0">
                          <svg className="h-5 w-5 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
                          </svg>
                        </div>
                      </div>
                    </motion.div>
                  ))}
                  
                  {contracts.length === 0 && (
                    <div className="text-center py-12">
                      <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                      </svg>
                      <h3 className="mt-2 text-sm font-medium text-gray-900">No contracts available</h3>
                      <p className="mt-1 text-sm text-gray-500">
                        Submit a contract to see AI scores and legal feedback.
                      </p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}


          {activeTab === 'contract-review' && (
            <div className="bg-white shadow overflow-hidden sm:rounded-lg">
              <div className="px-4 py-5 sm:px-6 border-b border-gray-200">
                <h3 className="text-lg leading-6 font-medium text-gray-900">Contract Review</h3>
                <p className="mt-1 max-w-2xl text-sm text-gray-500">Review and evaluate submitted contracts</p>
              </div>
              <div className="divide-y divide-gray-200">
                {contracts.map((contract) => (
                  <motion.div
                    key={contract.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.3 }}
                    className="px-4 py-4 hover:bg-gray-50 cursor-pointer"
                    onClick={() => setSelectedContract(contract)}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <div className="flex items-center justify-between">
                          <p className="text-sm font-medium text-indigo-600 truncate">
                            {contract.title}
                          </p>
                          <div className="ml-2 flex-shrink-0 flex">
                            <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusColor(contract.status)}`}>
                              {contract.status.replace('_', ' ')}
                            </span>
                          </div>
                        </div>
                        <div className="mt-2 flex flex-wrap gap-4">
                          <div className="flex items-center text-sm text-gray-500">
                            <strong>Department:</strong> {contract.department}
                          </div>
                          <div className="flex items-center text-sm text-gray-500">
                            <strong>Submitted by:</strong> {contract.submittedBy}
                          </div>
                          <div className="flex items-center text-sm text-gray-500">
                            <strong>Date:</strong> {contract.submittedDate}
                          </div>
                        </div>
                        <div className="mt-2">
                          <button
                            onClick={async (e) => {
                              e.stopPropagation();
                              try {
                                // Import jsPDF dynamically
                                const { jsPDF } = await import('jspdf');
                                
                                // Create PDF document
                                const doc = new jsPDF();
                                
                                // Set initial position
                                let yPosition = 20;
                                
                                // Add title
                                doc.setFontSize(20);
                                doc.setFont(undefined, 'bold');
                                doc.text(contract.title, 20, yPosition);
                                yPosition += 15;
                                
                                // Add metadata section
                                doc.setFontSize(12);
                                doc.setFont(undefined, 'normal');
                                
                                // Add metadata with proper formatting
                                doc.text(`Department: ${contract.department}`, 20, yPosition);
                                yPosition += 8;
                                doc.text(`Submitted by: ${contract.submittedBy}`, 20, yPosition);
                                yPosition += 8;
                                doc.text(`Date: ${contract.submittedDate}`, 20, yPosition);
                                yPosition += 8;
                                doc.text(`Status: ${contract.status}`, 20, yPosition);
                                yPosition += 8;
                                
                                if (contract.evaluationScore) {
                                  doc.text(`Evaluation Score: ${contract.evaluationScore}/100`, 20, yPosition);
                                  yPosition += 8;
                                }
                                
                                yPosition += 10; // Add some space
                                
                                // Add content section
                                doc.setFontSize(14);
                                doc.setFont(undefined, 'bold');
                                doc.text('Contract Document Content:', 20, yPosition);
                                yPosition += 10;
                                
                                // Add the actual content
                                doc.setFontSize(10);
                                doc.setFont(undefined, 'normal');
                                
                                // Check if summary has meaningful content
                                const hasContent = contract.summary && 
                                                  contract.summary.trim() && 
                                                  !contract.summary.includes('Contract document content will be available after completing the Q&A process');
                                
                                if (hasContent) {
                                  // Split the summary into lines that fit the PDF
                                  const lines = doc.splitTextToSize(contract.summary, 170);
                                  
                                  // Add each line to the PDF
                                  lines.forEach(line => {
                                    if (yPosition > 270) { // Check if we need a new page
                                      doc.addPage();
                                      yPosition = 20;
                                    }
                                    doc.text(line, 20, yPosition);
                                    yPosition += 6;
                                  });
                                } else {
                                  // Add detailed error message when no content is available
                                  const errorMessage = [
                                    "❌ ERROR: No draft content available for PDF generation",
                                    "",
                                    "Debug Information:",
                                    `- Contract Title: ${contract.title}`,
                                    `- Contract Status: ${contract.status}`,
                                    `- Has Summary: ${!!contract.summary}`,
                                    `- Summary Length: ${contract.summary ? contract.summary.length : 0}`,
                                    "",
                                    "Possible Issues:",
                                    "1. The contract may not have completed the Q&A process",
                                    "2. Draft content may not have been saved to database",
                                    "3. The draft generation process may have failed",
                                    "",
                                    "Please check the browser console for detailed debug logs."
                                  ];
                                  
                                  errorMessage.forEach(line => {
                                    if (yPosition > 270) { // Check if we need a new page
                                      doc.addPage();
                                      yPosition = 20;
                                    }
                                    doc.text(line, 20, yPosition);
                                    yPosition += 6;
                                  });
                                }
                                
                                // Save the PDF
                                doc.save(`${contract.title.replace(/[^a-z0-9]/gi, '_').toLowerCase()}_contract_document.pdf`);
                                
                              } catch (error) {
                                console.error('Error generating PDF:', error);
                                alert(`PDF Generation Error: ${error.message}\n\nCheck browser console for detailed debug information.`);
                              }
                            }}
                            className="bg-blue-600 hover:bg-blue-700 text-white py-1 px-3 rounded-md text-xs font-medium transition-colors duration-200"
                          >
                            📄 Download as PDF
                          </button>
                        </div>
                        {contract.evaluationScore && (
                          <div className="mt-2">
                            <span className="text-sm font-medium text-gray-500">
                              Evaluation Score: <span className="text-green-600">{contract.evaluationScore}/100</span>
                            </span>
                          </div>
                        )}
                      </div>
                      <div className="ml-5 flex-shrink-0">
                        <svg className="h-5 w-5 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
                        </svg>
                      </div>
                    </div>
                  </motion.div>
                ))}
                {contracts.length === 0 && (
                  <div className="text-center py-12">
                    <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                    </svg>
                    <h3 className="mt-2 text-sm font-medium text-gray-900">No contracts submitted</h3>
                    <p className="mt-1 text-sm text-gray-500">Get started by submitting your first contract.</p>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Evaluation Modal */}
      {selectedContract && (
        <div className="fixed inset-0 overflow-y-auto z-50">
          <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"></div>
            <span className="hidden sm:inline-block sm:align-middle sm:h-screen">&#8203;</span>
            <div className="inline-block align-bottom bg-white rounded-lg px-4 pt-5 pb-4 text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full sm:p-6">
              <div>
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-lg leading-6 font-medium text-gray-900">
                    {selectedContract.status === 'approved' || selectedContract.status === 'rejected' ? 'Edit Evaluation' : 'Evaluate Contract'}: {selectedContract.title}
                  </h3>
                  {selectedContract.status === 'approved' || selectedContract.status === 'rejected' ? (
                    <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusColor(selectedContract.status)}`}>
                      {selectedContract.status.replace('_', ' ')}
                    </span>
                  ) : null}
                </div>
                
                {selectedContract.evaluationScore && (
                  <div className="mb-4 p-3 bg-blue-50 rounded-md">
                    <p className="text-sm text-blue-700">
                      <strong>Current Score:</strong> {selectedContract.evaluationScore}/100
                    </p>
                    {selectedContract.reviewerFeedback && (
                      <p className="text-sm text-blue-700 mt-1">
                        <strong>Current Feedback:</strong> {selectedContract.reviewerFeedback}
                      </p>
                    )}
                  </div>
                )}
                
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Evaluation Score (0-100)
                  </label>
                  <input
                    type="number"
                    min="0"
                    max="100"
                    defaultValue={selectedContract.evaluationScore || ''}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Enter score"
                    id="scoreInput"
                  />
                </div>

                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Reviewer Feedback
                  </label>
                  <textarea
                    rows="4"
                    defaultValue={selectedContract.reviewerFeedback || ''}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Provide legal feedback and suggestions..."
                    id="feedbackInput"
                  />
                </div>
              </div>
              
              <div className="mt-5 sm:mt-6 sm:grid sm:grid-cols-3 sm:gap-3 sm:grid-flow-row-dense">
                <button
                  type="button"
                  className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-green-600 text-base font-medium text-white hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 sm:text-sm"
                  onClick={() => {
                    const score = parseInt(document.getElementById('scoreInput').value) || 0;
                    const feedback = document.getElementById('feedbackInput').value;
                    handleEvaluateContract(selectedContract.id, score, feedback, 'approved');
                  }}
                >
                  {selectedContract.status === 'approved' ? 'Update Approval' : 'Approve'}
                </button>
                <button
                  type="button"
                  className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-red-600 text-base font-medium text-white hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 sm:text-sm"
                  onClick={() => {
                    const score = parseInt(document.getElementById('scoreInput').value) || 0;
                    const feedback = document.getElementById('feedbackInput').value;
                    handleEvaluateContract(selectedContract.id, score, feedback, 'rejected');
                  }}
                >
                  {selectedContract.status === 'rejected' ? 'Update Rejection' : 'Reject'}
                </button>
                <button
                  type="button"
                  className="w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:text-sm"
                  onClick={() => setSelectedContract(null)}
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* AI Feedback Modal */}
      {selectedAiContract && (
        <div className="fixed inset-0 overflow-y-auto z-50">
          <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"></div>
            <span className="hidden sm:inline-block sm:align-middle sm:h-screen">&#8203;</span>
            <div className="inline-block align-bottom bg-white rounded-lg px-4 pt-5 pb-4 text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-2xl sm:w-full sm:p-6">
              <div>
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-lg leading-6 font-medium text-gray-900">
                    AI Legal Review: {selectedAiContract.title}
                  </h3>
                  <div className="flex items-center gap-2">
                    <span className={`px-3 py-1 rounded-full text-sm font-medium ${getScoreColor(selectedAiContract.aiScore)} bg-opacity-20`}>
                      AI Score: {selectedAiContract.aiScore}/100
                    </span>
                    <span className={`px-3 py-1 rounded-full text-sm font-medium ${getRiskColor(selectedAiContract.aiRiskLevel)}`}>
                      Risk: {selectedAiContract.aiRiskLevel}
                    </span>
                  </div>
                </div>
                
                {/* AI Feedback Section */}
                <div className="mb-6">
                  <h4 className="text-md font-semibold text-gray-900 mb-3">AI Legal Feedback</h4>
                  <div className="bg-blue-50 p-4 rounded-lg">
                    <p className="text-sm text-blue-700 leading-relaxed">
                      {selectedAiContract.aiFeedback || "No AI legal feedback available for this contract."}
                    </p>
                  </div>
                </div>
                
                {/* Contract Details */}
                <div className="bg-gray-50 p-4 rounded-lg mb-6">
                  <h4 className="text-md font-semibold text-gray-800 mb-2">Contract Details</h4>
                  <div className="text-sm text-gray-600 space-y-2">
                    <div className="flex justify-between">
                      <span><strong>Department:</strong></span>
                      <span>{selectedAiContract.department}</span>
                    </div>
                    <div className="flex justify-between">
                      <span><strong>Submitted by:</strong></span>
                      <span>{selectedAiContract.submittedBy}</span>
                    </div>
                    <div className="flex justify-between">
                      <span><strong>Date:</strong></span>
                      <span>{selectedAiContract.submittedDate}</span>
                    </div>
                    <div className="flex justify-between">
                      <span><strong>Status:</strong></span>
                      <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusColor(selectedAiContract.status)}`}>
                        {selectedAiContract.status.replace('_', ' ')}
                      </span>
                    </div>
                    {selectedAiContract.evaluationScore && (
                      <div className="flex justify-between">
                        <span><strong>Human Score:</strong></span>
                        <span className="text-green-600">{selectedAiContract.evaluationScore}/100</span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
              
              <div className="mt-5 sm:mt-6">
                <button
                  type="button"
                  className="w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:text-sm"
                  onClick={() => setSelectedAiContract(null)}
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ContractReviewerDashboard;
