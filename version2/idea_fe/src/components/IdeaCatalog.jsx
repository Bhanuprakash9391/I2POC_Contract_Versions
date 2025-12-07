import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';

const IdeaCatalog = () => {
  const [ideas, setIdeas] = useState([]);
  const [filter, setFilter] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(true);
  const [selectedIdea, setSelectedIdea] = useState(null);

  // Fetch real data from API
  useEffect(() => {
    const fetchIdeas = async () => {
      try {
        const response = await fetch('/apcontract/contracts');
        if (response.ok) {
          const data = await response.json();
          // Transform API data to match component format
          // Remove duplicates by using a Map with session_id as key
          const ideaMap = new Map();
          data.ideas.forEach(idea => {
            // Use session_id as unique key to prevent duplicates
            if (!ideaMap.has(idea.session_id)) {
              // Generate full draft text from all_drafts
              const generateFullDraft = () => {
                // Get all drafts from the idea
                const allDrafts = idea.all_drafts || idea.drafts || {};
                
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
                const conversationHistory = idea.conversation_history || idea.metadata?.conversation_history || [];
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
                return idea.idea || idea.rephrased_idea || idea.description || 'Idea details will be available after contract completion';
              };
              
              const fullDraft = generateFullDraft();
              
              ideaMap.set(idea.session_id, {
                id: idea.session_id,
                title: idea.title || 'Untitled Idea',
                department: idea.metadata?.department || 'General',
                status: (idea.status === 'completed' || idea.status === 'in_progress') ? 'submitted' : idea.status || 'submitted', // Convert completed/in_progress to submitted
                submittedBy: idea.metadata?.submitted_by || 'Anonymous',
                submittedDate: idea.metadata?.created_at ? new Date(idea.metadata.created_at).toISOString().split('T')[0] : 'Unknown',
                evaluationScore: idea.metadata?.evaluation_score || idea.evaluation_score || idea.ai_score || null,
                reviewerFeedback: idea.metadata?.reviewer_feedback || idea.reviewer_feedback || null,
                summary: fullDraft,
                category: idea.metadata?.category || 'General'
              });
            }
          });
          const transformedIdeas = Array.from(ideaMap.values());
          setIdeas(transformedIdeas);
        } else {
          console.error('Failed to fetch ideas:', response.status);
          // Fallback to empty array if API fails
          setIdeas([]);
        }
      } catch (error) {
        console.error('Error fetching ideas:', error);
        setIdeas([]);
      } finally {
        setLoading(false);
      }
    };

    fetchIdeas();
  }, []);

  const filteredIdeas = ideas.filter(idea => {
    const matchesFilter = filter === 'all' || idea.status === filter;
    const matchesSearch = idea.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         idea.summary.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         idea.department.toLowerCase().includes(searchTerm.toLowerCase());
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
    total: ideas.length,
    pending_review: ideas.filter(i => i.status === 'submitted').length, // Only submitted ideas are pending review
    approved: ideas.filter(i => i.status === 'approved').length,
    rejected: ideas.filter(i => i.status === 'rejected').length
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading ideas catalog...</p>
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
                <dt className="text-sm font-medium text-gray-500 truncate">Total Ideas</dt>
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
                  placeholder="Search ideas by title, department, or description..."
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

          {/* Ideas Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredIdeas.map((idea) => (
              <motion.div
                key={idea.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3 }}
                className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow duration-300 cursor-pointer"
                onClick={() => setSelectedIdea(idea)}
              >
                <div className="p-6">
                  <div className="flex justify-between items-start mb-3">
                    <h3 className="text-lg font-semibold text-gray-900 line-clamp-2 flex-1 mr-2">
                      {idea.title}
                    </h3>
                    <span className={`px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(idea.status)}`}>
                      {idea.status.replace('_', ' ')}
                    </span>
                  </div>

                  <div className="mb-3">
                    <span className={`px-2 py-1 text-xs font-semibold rounded-full ${getCategoryColor(idea.category)}`}>
                      {idea.category}
                    </span>
                  </div>


                  <div className="space-y-2 text-sm text-gray-500">
                    <div className="flex justify-between">
                      <span>Department:</span>
                      <span className="font-medium">{idea.department}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Submitted by:</span>
                      <span className="font-medium">{idea.submittedBy}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Date:</span>
                      <span className="font-medium">{idea.submittedDate}</span>
                    </div>
                    {(idea.evaluationScore || idea.aiScore) && (
                      <div className="flex justify-between">
                        <span>Score:</span>
                        <span className={`font-medium ${(idea.evaluationScore || idea.aiScore) >= 70 ? 'text-green-600' : (idea.evaluationScore || idea.aiScore) >= 50 ? 'text-yellow-600' : 'text-red-600'}`}>
                          {(idea.evaluationScore || idea.aiScore)}/100
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              </motion.div>
            ))}
          </div>

          {/* Idea Detail Modal */}
          {selectedIdea && (
            <div className="fixed inset-0 overflow-y-auto z-50">
              <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
                <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"></div>
                <span className="hidden sm:inline-block sm:align-middle sm:h-screen">&#8203;</span>
                <div className="inline-block align-bottom bg-white rounded-lg px-4 pt-5 pb-4 text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-2xl sm:w-full sm:p-6">
                  <div>
                    <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
                      {selectedIdea.title}
                    </h3>
                    
                    <div className="mb-4">
                      <div className="flex items-center space-x-2 mb-2">
                        <span className={`px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(selectedIdea.status)}`}>
                          {selectedIdea.status.replace('_', ' ')}
                        </span>
                        <span className={`px-2 py-1 text-xs font-semibold rounded-full ${getCategoryColor(selectedIdea.category)}`}>
                          {selectedIdea.category}
                        </span>
                      </div>
                    </div>


                    <div className="grid grid-cols-2 gap-4 text-sm text-gray-500">
                      <div>
                        <span className="font-medium">Department:</span> {selectedIdea.department}
                      </div>
                      <div>
                        <span className="font-medium">Submitted by:</span> {selectedIdea.submittedBy}
                      </div>
                      <div>
                        <span className="font-medium">Date:</span> {selectedIdea.submittedDate}
                      </div>
                      {(selectedIdea.evaluationScore || selectedIdea.aiScore) && (
                        <div>
                          <span className="font-medium">Score:</span> 
                          <span className={`ml-1 ${(selectedIdea.evaluationScore || selectedIdea.aiScore) >= 70 ? 'text-green-600' : (selectedIdea.evaluationScore || selectedIdea.aiScore) >= 50 ? 'text-yellow-600' : 'text-red-600'}`}>
                            {(selectedIdea.evaluationScore || selectedIdea.aiScore)}/100
                          </span>
                        </div>
                      )}
                    </div>

                    {/* Show evaluation details for accepted/rejected ideas */}
                    {(selectedIdea.status === 'approved' || selectedIdea.status === 'rejected') && (
                      <div className="mt-4 border-t pt-4">
                        <h4 className="text-sm font-medium text-gray-700 mb-2">Reviewer Evaluation</h4>
                        {selectedIdea.evaluationScore && (
                          <div className="mb-2">
                            <span className="font-medium">Score:</span> 
                            <span className={`ml-2 ${selectedIdea.evaluationScore >= 70 ? 'text-green-600' : selectedIdea.evaluationScore >= 50 ? 'text-yellow-600' : 'text-red-600'}`}>
                              {selectedIdea.evaluationScore}/100
                            </span>
                          </div>
                        )}
                        {selectedIdea.reviewerFeedback && (
                          <div>
                            <span className="font-medium">Feedback:</span>
                            <div className="mt-1 bg-gray-50 p-3 rounded-md">
                              <p className="text-sm text-gray-600 whitespace-pre-wrap">{selectedIdea.reviewerFeedback}</p>
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
                      onClick={() => setSelectedIdea(null)}
                    >
                      Close
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {filteredIdeas.length === 0 && (
            <div className="text-center py-12">
              <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
              <h3 className="mt-2 text-sm font-medium text-gray-900">No ideas found</h3>
              <p className="mt-1 text-sm text-gray-500">
                {searchTerm || filter !== 'all' 
                  ? 'Try adjusting your search or filter criteria'
                  : 'Be the first to submit an idea!'}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default IdeaCatalog;
