import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';

const ContractCatalog = () => {
  const [contracts, setContracts] = useState([]);
  const [filter, setFilter] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(true);
  const [selectedContract, setSelectedContract] = useState(null);

  // Fetch real data from API
  useEffect(() => {
    const fetchContracts = async () => {
      try {
        const response = await fetch('/apcontract/contracts');
        if (response.ok) {
          const data = await response.json();
          // Transform API data to match component format
          // Remove duplicates by using a Map with session_id as key
          const contractMap = new Map();
          data.ideas.forEach(contract => {
            // Use session_id as unique key to prevent duplicates
            if (!contractMap.has(contract.session_id)) {
              // Generate full draft text from all_drafts
              const generateFullDraft = () => {
                // Get all drafts from the contract
                const allDrafts = contract.all_drafts || contract.drafts || {};
                
                if (Object.keys(allDrafts).length > 0) {
                  // Combine all section drafts into a complete document
                  let fullDraft = '';
                  Object.entries(allDrafts).forEach(([section, draft]) => {
                    if (draft && draft.trim()) {
                      fullDraft += `## ${section}\n\n${draft}\n\n`;
                    }
                  });
                  
                  if (fullDraft.trim()) {
                    return fullDraft;
                  }
                }
                
                // Fallback to conversation history if no drafts available
                const conversationHistory = contract.conversation_history || contract.metadata?.conversation_history || [];
                if (conversationHistory && conversationHistory.length > 0) {
                  const userResponses = conversationHistory
                    .filter(msg => msg.role === 'user' || msg.type === 'user')
                    .map(msg => msg.content || msg.message || '')
                    .filter(text => text && text.length > 10);
                  
                  if (userResponses.length > 0) {
                    return userResponses.join('\n\n');
                  }
                }
                
                // Final fallback
                return contract.idea || contract.rephrased_idea || contract.description || 'Contract details will be available after completion';
              };
              
              const fullDraft = generateFullDraft();
              
              contractMap.set(contract.session_id, {
                id: contract.session_id,
                title: contract.title || 'Untitled Contract',
                department: contract.metadata?.department || 'General',
                status: (contract.status === 'completed' || contract.status === 'in_progress') ? 'submitted' : contract.status || 'submitted', // Convert completed/in_progress to submitted
                submittedBy: contract.metadata?.submitted_by || 'Anonymous',
                submittedDate: contract.metadata?.created_at ? new Date(contract.metadata.created_at).toISOString().split('T')[0] : 'Unknown',
                evaluationScore: contract.metadata?.evaluation_score || contract.evaluation_score || null,
                reviewerFeedback: contract.metadata?.reviewer_feedback || contract.reviewer_feedback || null,
                summary: fullDraft,
                category: contract.metadata?.category || 'General'
              });
            }
          });
          const transformedContracts = Array.from(contractMap.values());
          setContracts(transformedContracts);
        } else {
          console.error('Failed to fetch contracts:', response.status);
          // Fallback to empty array if API fails
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

  const filteredContracts = contracts.filter(contract => {
    const matchesFilter = filter === 'all' || contract.status === filter;
    const matchesSearch = contract.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         contract.summary.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         contract.department.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesFilter && matchesSearch;
  });

  const getStatusColor = (status) => {
    switch (status) {
      case 'submitted': return 'bg-yellow-100 text-yellow-800';
      case 'approved': return 'bg-green-100 text-green-800';
      case 'rejected': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getCategoryColor = (category) => {
    switch (category) {
      case 'AI & Automation': return 'bg-purple-100 text-purple-800';
      case 'Analytics & Reporting': return 'bg-indigo-100 text-indigo-800';
      case 'Process Automation': return 'bg-teal-100 text-teal-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const stats = {
    total: contracts.length,
    pending_review: contracts.filter(i => i.status === 'submitted').length, // Only submitted contracts are pending review
    approved: contracts.filter(i => i.status === 'approved').length,
    rejected: contracts.filter(i => i.status === 'rejected').length
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading contract catalog...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          {/* Stats Overview */}
          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4 mb-8">
            <div className="bg-white overflow-hidden shadow rounded-lg">
              <div className="px-4 py-5 sm:p-6">
                <dt className="text-sm font-medium text-gray-500 truncate">Total Contracts</dt>
                <dd className="mt-1 text-3xl font-semibold text-gray-900">{stats.total}</dd>
              </div>
            </div>
            <div className="bg-white overflow-hidden shadow rounded-lg">
              <div className="px-4 py-5 sm:p-6">
                <dt className="text-sm font-medium text-gray-500 truncate">Pending Review</dt>
                <dd className="mt-1 text-3xl font-semibold text-yellow-600">{stats.pending_review}</dd>
              </div>
            </div>
            <div className="bg-white overflow-hidden shadow rounded-lg">
              <div className="px-4 py-5 sm:p-6">
                <dt className="text-sm font-medium text-gray-500 truncate">Approved</dt>
                <dd className="mt-1 text-3xl font-semibold text-green-600">{stats.approved}</dd>
              </div>
            </div>
            <div className="bg-white overflow-hidden shadow rounded-lg">
              <div className="px-4 py-5 sm:p-6">
                <dt className="text-sm font-medium text-gray-500 truncate">Rejected</dt>
                <dd className="mt-1 text-3xl font-semibold text-red-600">{stats.rejected}</dd>
              </div>
            </div>
          </div>

          {/* Filters and Search */}
          <div className="mb-6 bg-white p-4 rounded-lg shadow">
            <div className="flex flex-col sm:flex-row gap-4">
              <div className="flex-1">
                <input
                  type="text"
                  placeholder="Search contracts by title, department, or description..."
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
              </div>
              <div className="flex gap-2">
                <select
                  className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  value={filter}
                  onChange={(e) => setFilter(e.target.value)}
                >
                  <option value="all">All Status</option>
                  <option value="submitted">Submitted</option>
                  <option value="approved">Approved</option>
                  <option value="rejected">Rejected</option>
                </select>
              </div>
            </div>
          </div>

          {/* Contracts Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredContracts.map((contract) => (
              <motion.div
                key={contract.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3 }}
                className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow duration-300 cursor-pointer"
                onClick={() => setSelectedContract(contract)}
              >
                <div className="p-6">
                  <div className="flex justify-between items-start mb-3">
                    <h3 className="text-lg font-semibold text-gray-900 line-clamp-2 flex-1 mr-2">
                      {contract.title}
                    </h3>
                    <span className={`px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(contract.status)}`}>
                      {contract.status.replace('_', ' ')}
                    </span>
                  </div>

                  <div className="mb-3">
                    <span className={`px-2 py-1 text-xs font-semibold rounded-full ${getCategoryColor(contract.category)}`}>
                      {contract.category}
                    </span>
                  </div>


                  <div className="space-y-2 text-sm text-gray-500">
                    <div className="flex justify-between">
                      <span>Department:</span>
                      <span className="font-medium">{contract.department}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Submitted by:</span>
                      <span className="font-medium">{contract.submittedBy}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Date:</span>
                      <span className="font-medium">{contract.submittedDate}</span>
                    </div>
                    {contract.evaluationScore && (
                      <div className="flex justify-between">
                        <span>Score:</span>
                        <span className={`font-medium ${contract.evaluationScore >= 70 ? 'text-green-600' : contract.evaluationScore >= 50 ? 'text-yellow-600' : 'text-red-600'}`}>
                          {contract.evaluationScore}/100
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              </motion.div>
            ))}
          </div>

          {/* Contract Detail Modal */}
          {selectedContract && (
            <div className="fixed inset-0 overflow-y-auto z-50">
              <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
                <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"></div>
                <span className="hidden sm:inline-block sm:align-middle sm:h-screen">&#8203;</span>
                <div className="inline-block align-bottom bg-white rounded-lg px-4 pt-5 pb-4 text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-2xl sm:w-full sm:p-6">
                  <div>
                    <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
                      {selectedContract.title}
                    </h3>
                    
                    <div className="mb-4">
                      <div className="flex items-center space-x-2 mb-2">
                        <span className={`px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(selectedContract.status)}`}>
                          {selectedContract.status.replace('_', ' ')}
                        </span>
                        <span className={`px-2 py-1 text-xs font-semibold rounded-full ${getCategoryColor(selectedContract.category)}`}>
                          {selectedContract.category}
                        </span>
                      </div>
                    </div>


                    <div className="grid grid-cols-2 gap-4 text-sm text-gray-500">
                      <div>
                        <span className="font-medium">Department:</span> {selectedContract.department}
                      </div>
                      <div>
                        <span className="font-medium">Submitted by:</span> {selectedContract.submittedBy}
                      </div>
                      <div>
                        <span className="font-medium">Date:</span> {selectedContract.submittedDate}
                      </div>
                      {selectedContract.evaluationScore && (
                        <div>
                          <span className="font-medium">Score:</span> 
                          <span className={`ml-1 ${selectedContract.evaluationScore >= 70 ? 'text-green-600' : selectedContract.evaluationScore >= 50 ? 'text-yellow-600' : 'text-red-600'}`}>
                            {selectedContract.evaluationScore}/100
                          </span>
                        </div>
                      )}
                    </div>

                    {/* Show evaluation details for accepted/rejected contracts */}
                    {(selectedContract.status === 'approved' || selectedContract.status === 'rejected') && (
                      <div className="mt-4 border-t pt-4">
                        <h4 className="text-sm font-medium text-gray-700 mb-2">Reviewer Evaluation</h4>
                        {selectedContract.evaluationScore && (
                          <div className="mb-2">
                            <span className="font-medium">Score:</span> 
                            <span className={`ml-2 ${selectedContract.evaluationScore >= 70 ? 'text-green-600' : selectedContract.evaluationScore >= 50 ? 'text-yellow-600' : 'text-red-600'}`}>
                              {selectedContract.evaluationScore}/100
                            </span>
                          </div>
                        )}
                        {selectedContract.reviewerFeedback && (
                          <div>
                            <span className="font-medium">Feedback:</span>
                            <div className="mt-1 bg-gray-50 p-3 rounded-md">
                              <p className="text-sm text-gray-600 whitespace-pre-wrap">{selectedContract.reviewerFeedback}</p>
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                  
                  <div className="mt-5 sm:mt-6">
                    <button
                      type="button"
                      className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-blue-600 text-base font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:text-sm"
                      onClick={() => setSelectedContract(null)}
                    >
                      Close
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {filteredContracts.length === 0 && (
            <div className="text-center py-12">
              <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
              <h3 className="mt-2 text-sm font-medium text-gray-900">No contracts found</h3>
              <p className="mt-1 text-sm text-gray-500">
                {searchTerm || filter !== 'all' 
                  ? 'Try adjusting your search or filter criteria'
                  : 'Be the first to submit a contract!'}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ContractCatalog;
