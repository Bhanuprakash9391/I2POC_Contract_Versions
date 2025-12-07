import { createContext, useContext, useEffect, useState } from "react";
import { chatWithDraftAgent } from "./utils/app";

const BASE_URL = '/apcontract';
const ChatContext = createContext();

export function ChatProvider({ children }) {
  const [messages, setMessages] = useState([]);
  const [draftMessages, setDraftMessages] = useState([]);
  const [drafts, setDrafts] = useState({});
  const [input, setInput] = useState("");
  const [initialChatStep, setInitialChatStep] = useState("idea-submission");
  const [contractSections, setContractSections] = useState([]);
  const [session_id, setSession_id] = useState("");
  const [titles, setTitles] = useState([]);
  const [selectedTitle, setSelectedTitle] = useState("");
  const [rephrasedIdea, setRephrasedIdea] = useState("");
  const [activeSection, setActiveSection] = useState("");
  const [isReviewedSectionDraftActive, setIsReviewedSectionDraftActive] = useState(false);
  const [isDraftingComplete, setIsDraftingComplete] = useState(false);
  const [userContext, setUserContext] = useState(null);
  const [loading, setLoading] = useState(false);

  console.log({ loading });
  useEffect(() => {
    if (contractSections.length > 0) {
      contractSections.forEach((step) => {
        setDrafts((prev) => ({
          ...prev,
          [step.section_heading]: `Currently we have not completed this section.`,
        }));
      });
    }
  }, [contractSections]);

  const idea_structuring = { 
    idea: rephrasedIdea, 
    title: selectedTitle, 
    all_sections: contractSections,
    user_context: userContext
  };

  const handleSend = async () => {
    console.log("handleSend called");
    if (!input.trim()) return;
    // Add user message to the chat
    const userMessage = { role: "user", content: input };
    const updatedMessages = [...messages, userMessage];
    setMessages(updatedMessages);

    // Store the user input before clearing it
    const userInput = input;
    setInput("");

    try {
      setLoading(true);
      if (initialChatStep === "idea-submission") {
        // Use the existing chatWithDraftAgent function but handle responses properly
        let res = await chatWithDraftAgent(session_id, userInput, false, idea_structuring);
        
        // Parse the response with better error handling
        try {
          if (res.startsWith("data: ")) {
            res = JSON.parse(res?.slice(6));
          } else {
            res = JSON.parse(res);
          }
        } catch (parseError) {
          console.error("JSON parsing error:", parseError);
          console.error("Raw response:", res);
          throw new Error(`Failed to parse server response: ${parseError.message}`);
        }
        
        console.log("🚀 ~ handleSend ~ res:", res);
        
        // Handle different response types
        if (res.type === "interrupt") {
          if (res.action === "get_question_response") {
            // AI is asking a question - add it to messages
            setMessages(prev => [...prev, { 
              role: "assistant", 
              content: res.question,
              reason: res.reason,
              section: res.section,
              subsection: res.subsection
            }]);
            setInitialChatStep("question-response");
          } else if (res.action === "get_structure_review") {
            // AI wants structure review
            setSession_id(res.session_id);
            setContractSections(res.all_sections);
            setSelectedTitle(res.title);
            setRephrasedIdea(res.idea);
            setInitialChatStep("structure-review");
          }
        } else if (res.type === "end") {
          // Document completion
          console.log("Document completed:", res);
        }
      } else if (initialChatStep === "question-response") {
        // User is answering a question - continue the conversation
        let res = await chatWithDraftAgent(session_id, userInput, true, idea_structuring);
        
        // Parse the response with better error handling
        try {
          if (res.startsWith("data: ")) {
            res = JSON.parse(res?.slice(6));
          } else {
            res = JSON.parse(res);
          }
        } catch (parseError) {
          console.error("JSON parsing error:", parseError);
          console.error("Raw response:", res);
          throw new Error(`Failed to parse server response: ${parseError.message}`);
        }
        
        console.log("🚀 ~ handleSend ~ question response:", res);
        
        // Handle the response to the question
        if (res.type === "interrupt") {
          if (res.action === "get_question_response") {
            // AI asks another question
            setMessages(prev => [...prev, { 
              role: "assistant", 
              content: res.question,
              reason: res.reason,
              section: res.section,
              subsection: res.subsection
            }]);
            // Stay in question-response mode
          } else if (res.action === "get_structure_review") {
            // Move to structure review
            setSession_id(res.session_id);
            setContractSections(res.all_sections);
            setSelectedTitle(res.title);
            setRephrasedIdea(res.idea);
            setInitialChatStep("structure-review");
          }
        }
      }
    } catch (error) {
      // Add error message to the updated messages array
      const errorMessage = error.message || "An unexpected error occurred";
      console.error("Error during chat interaction:", errorMessage);
      
      // Provide more specific error messages
      let userErrorMessage = "I apologize, but I encountered an error. Please try again.";
      
      if (errorMessage.includes("Failed to fetch") || errorMessage.includes("Network Error")) {
        userErrorMessage = "Network connection error. Please check your internet connection and try again.";
      } else if (errorMessage.includes("Empty response")) {
        userErrorMessage = "The server returned an empty response. Please try again.";
      } else if (errorMessage.includes("HTTP error")) {
        userErrorMessage = "Server connection error. Please ensure the backend server is running.";
      }
      
      setMessages([...updatedMessages, { role: "assistant", content: userErrorMessage }]);
    } finally {
      setLoading(false);
    }
  };

  const handleDraftChat = async () => {
    if (!input.trim() && activeSection && !isReviewedSectionDraftActive) return;
    setLoading(true);
    let updatedMessages = [...draftMessages];
    if (activeSection && !isReviewedSectionDraftActive) {
      // Add user message to the chat
      const userMessage = { role: "user", content: input };
      updatedMessages = [...draftMessages, userMessage];
      setDraftMessages(updatedMessages);
    }

    // Store the user input before clearing it
    const userInput = isReviewedSectionDraftActive ? drafts[activeSection] : input;
    setInput("");
    try {
      let res = await chatWithDraftAgent(session_id, userInput, true, idea_structuring);
      setIsReviewedSectionDraftActive(false);
      
      // Parse the response with better error handling
      try {
        if (res.startsWith("data: ")) {
          res = JSON.parse(res?.slice(6));
        } else {
          res = JSON.parse(res);
        }
      } catch (parseError) {
        console.error("JSON parsing error:", parseError);
        console.error("Raw response:", res);
        throw new Error(`Failed to parse server response: ${parseError.message}`);
      }
      console.log("🚀 ~ submitIdea ~ res:", res);
      const { action, section, question, reason, draft } = res;
      action != "generate_document" && setActiveSection(section);

      if (action == "generate_document" && res?.final_state?.all_drafts) {
        setDrafts(res?.final_state?.all_drafts);
        setIsDraftingComplete(true);
        setDraftMessages([...updatedMessages, { role: "assistant", content: "## **We have completed all the sections. Download the draft from draft section.**" }]);
      } else if (action == "get_question_response") {
        const newDraft = { ...drafts, [section]: draft };
        console.log("draft ===>", newDraft);
        setDraftMessages([...updatedMessages, { role: "assistant", content: `${question}`, reason: `${reason}` }]);
        draft && draft.length > 0 && setDrafts(newDraft);
      } else if (action == "get_reviewed_section_draft") {
        setIsReviewedSectionDraftActive(true);
        setDraftMessages([
          ...updatedMessages,
          {
            role: "assistant",
            content: `Please check the **${activeSection}** section draft.\n\nIf you like the draft click on the **Continue** button, or edit the draft`,
          },
        ]);
        const newDraft = { ...drafts, [section]: draft };
        console.log("draft ===>", newDraft);
        setDrafts(newDraft);
      } else if (action == "get_review_changes") {
        setDraftMessages([...updatedMessages, { role: "assistant", content: "Please reply with the changes you want to make." }]);
      }
    } catch (error) {
      // Add error message to the updated messages array
      setDraftMessages([...updatedMessages, { role: "assistant", content: "I apologize, but I encountered an error. Please try again." }]);
      const errorMessage = error.response?.data?.message || "An unexpected error occurred";
      console.error("Error during chat interaction:", errorMessage);
    } finally {
      setLoading(false);
    }
  };
  console.log("draft", { draftMessages, drafts });

  const handleNewChat = () => {
    setInitialChatStep("idea-submission");
    setContractSections([]);
    setSession_id("");
    setTitles([]);
    setSelectedTitle("");
    setMessages([]);
    setDraftMessages([]);
    setDrafts({});
    setActiveSection("");
    setInput("");
    setLoading(false);
    setRephrasedIdea("");
    setIsDraftingComplete(false);
    setIsReviewedSectionDraftActive(false);
    setUserContext(null);
  };

  return (
    <ChatContext.Provider
      value={{
        messages,
        setMessages,
        input,
        setInput,
        handleSend,
        handleNewChat,
        initialChatStep,
        setInitialChatStep,
        contractSections,
        setContractSections,
        titles,
        setTitles,
        selectedTitle,
        setSelectedTitle,
        session_id,
        setSession_id,
        handleDraftChat,
        draftMessages,
        drafts,
        setDrafts,
        activeSection,
        loading,
        rephrasedIdea,
        setRephrasedIdea,
        isReviewedSectionDraftActive,
        setIsReviewedSectionDraftActive,
        isDraftingComplete,
        userContext,
        setUserContext,
      }}
    >
      {children}
    </ChatContext.Provider>
  );
}

export function useChat() {
  return useContext(ChatContext);
}
