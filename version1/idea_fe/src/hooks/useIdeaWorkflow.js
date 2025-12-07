import { useState, useCallback } from 'react';
import apiService from '../services/apiService';

/**
 * Custom hook for managing the idea workflow state and API calls
 * @returns {Object} Hook state and methods
 */
export const useIdeaWorkflow = () => {
  const [state, setState] = useState({
    // Current step in the workflow
    currentStep: 'initial', // 'initial', 'submitted', 'approved', 'titles-generated', 'completed'
    
    // Loading states
    isLoading: false,
    
    // Data from each step
    originalIdea: '',
    rephrasedIdea: '',
    sessionId: null,
    generatedTitles: [],
    selectedTitle: '',
    projectStructure: null,
    
    // Error handling
    error: null,
    
    // Progress tracking
    progress: {
      ideaSubmitted: false,
      ideaApproved: false,
      titlesGenerated: false,
      titleSelected: false
    }
  });

  // Reset the workflow
  const resetWorkflow = useCallback(() => {
    setState({
      currentStep: 'initial',
      isLoading: false,
      originalIdea: '',
      rephrasedIdea: '',
      sessionId: null,
      generatedTitles: [],
      selectedTitle: '',
      projectStructure: null,
      error: null,
      progress: {
        ideaSubmitted: false,
        ideaApproved: false,
        titlesGenerated: false,
        titleSelected: false
      }
    });
  }, []);

  // Step 1: Submit idea
  const submitIdea = useCallback(async (query) => {
    setState(prev => ({ ...prev, isLoading: true, error: null, originalIdea: query }));
    
    try {
      const response = await apiService.submitIdea(query);
      
      setState(prev => ({
        ...prev,
        isLoading: false,
        currentStep: 'submitted',
        rephrasedIdea: response.rephrased_idea,
        sessionId: response.session_id,
        progress: { ...prev.progress, ideaSubmitted: true }
      }));
      
      return response;
    } catch (error) {
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: error.message || 'Failed to submit idea'
      }));
      throw error;
    }
  }, []);

  // Step 2: Approve idea
  const approveIdea = useCallback(async (approval = 'yes') => {
    if (!state.sessionId) {
      throw new Error('No session ID available. Please submit an idea first.');
    }

    setState(prev => ({ ...prev, isLoading: true, error: null }));
    
    try {
      const response = await apiService.approveIdea(state.sessionId, approval);
      
      setState(prev => ({
        ...prev,
        isLoading: false,
        currentStep: 'approved',
        projectStructure: response.output,
        progress: { ...prev.progress, ideaApproved: true }
      }));
      
      return response;
    } catch (error) {
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: error.message || 'Failed to approve idea'
      }));
      throw error;
    }
  }, [state.sessionId]);

  // Step 3: Generate titles
  const generateTitles = useCallback(async (inputData) => {
    if (!state.sessionId) {
      throw new Error('No session ID available. Please submit and approve an idea first.');
    }

    setState(prev => ({ ...prev, isLoading: true, error: null }));
    
    try {
      const response = await apiService.generateTitles(state.sessionId, inputData);
      
      setState(prev => ({
        ...prev,
        isLoading: false,
        currentStep: 'titles-generated',
        generatedTitles: response.titles,
        progress: { ...prev.progress, titlesGenerated: true }
      }));
      
      return response;
    } catch (error) {
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: error.message || 'Failed to generate titles'
      }));
      throw error;
    }
  }, [state.sessionId]);

  // Step 4: Select title
  const selectTitle = useCallback(async (title, inputData) => {
    if (!state.sessionId) {
      throw new Error('No session ID available. Please complete previous steps first.');
    }

    setState(prev => ({ ...prev, isLoading: true, error: null, selectedTitle: title }));
    
    try {
      const response = await apiService.selectTitle(state.sessionId, title, inputData);
      
      setState(prev => ({
        ...prev,
        isLoading: false,
        currentStep: 'completed',
        projectStructure: response.output,
        progress: { ...prev.progress, titleSelected: true }
      }));
      
      return response;
    } catch (error) {
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: error.message || 'Failed to select title'
      }));
      throw error;
    }
  }, [state.sessionId]);

  // Complete workflow in one go
  const completeWorkflow = useCallback(async (originalQuery, selectedTitle) => {
    setState(prev => ({ ...prev, isLoading: true, error: null }));
    
    try {
      const result = await apiService.completeIdeaWorkflow(originalQuery, selectedTitle);
      
      setState(prev => ({
        ...prev,
        isLoading: false,
        currentStep: 'completed',
        originalIdea: originalQuery,
        rephrasedIdea: result.ideaSubmission.rephrased_idea,
        sessionId: result.ideaSubmission.session_id,
        generatedTitles: result.titles.titles,
        selectedTitle: selectedTitle,
        projectStructure: result.final.output,
        progress: {
          ideaSubmitted: true,
          ideaApproved: true,
          titlesGenerated: true,
          titleSelected: true
        }
      }));
      
      return result;
    } catch (error) {
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: error.message || 'Failed to complete workflow'
      }));
      throw error;
    }
  }, []);

  // Clear error
  const clearError = useCallback(() => {
    setState(prev => ({ ...prev, error: null }));
  }, []);

  // Get current section info
  const getCurrentSection = useCallback(() => {
    if (!state.projectStructure) return null;
    
    return {
      name: state.projectStructure.current_section,
      subsections: state.projectStructure.current_subsections,
      progress: state.projectStructure.progress,
      allSections: state.projectStructure.sections
    };
  }, [state.projectStructure]);

  return {
    // State
    ...state,
    
    // Actions
    submitIdea,
    approveIdea,
    generateTitles,
    selectTitle,
    completeWorkflow,
    resetWorkflow,
    clearError,
    
    // Computed values
    getCurrentSection,
    
    // Helper flags
    canApprove: state.currentStep === 'submitted',
    canGenerateTitles: state.currentStep === 'approved',
    canSelectTitle: state.currentStep === 'titles-generated',
    isCompleted: state.currentStep === 'completed'
  };
};

export default useIdeaWorkflow;