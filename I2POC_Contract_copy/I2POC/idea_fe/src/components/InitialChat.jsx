// GoldenPurpleChat.jsx
import React, { useEffect, useRef } from "react";
import { motion } from "framer-motion";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import "./InitialChat.css";
// Using Tailwind CSS instead of CSS file
import { useChat } from "../ChatContext";
// import SelectableList from "./SelectableList";
import ContractSectionsDisplay from "./DraftChat/ContractSectionsDisplay";

// const BASE_URL = "http://127.0.0.1:8000";
// const BASE_URL = "http://34.63.96.127:8000";

export default function GoldenPurpleChat() {
  const {
    messages,
    input,
    setInput,
    handleSend,
    handleNewChat,
    initialChatStep,
    // titles,
    contractSections,
    // setInitialChatStep,
    selectedTitle,
    rephrasedIdea,
    // session_id,
    setSelectedTitle,
    setRephrasedIdea,
    loading,
  } = useChat();
  const messagesEndRef = useRef(null);
  console.log({ loading });

  // Auto-scroll to bottom when messages change or loading state changes
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const handleContentUpdate = async (e, type) => {
    const content = e.target.textContent;
    // const updateData = {
    //   session_id,
    //   title: type === "title" ? content : selectedTitle,
    //   idea: type === "idea" ? content : rephrasedIdea,
    // };

    try {
      // const response = await axios.post(`${BASE_URL}/submit-changes/`, updateData);

      // Update local state based on type
      if (type === "title") {
        setSelectedTitle(content);
      } else {
        setRephrasedIdea(content);
      }
    } catch (error) {
      console.error(`Error updating ${type}:`, error);
    }
  };

  console.log("messages:", messages);

  return (
    <div className="chat-container">

      {messages.length == 0 && (
        <div className="flex flex-col items-center justify-center align-middle text-center" style={{ minHeight: "500px" }}>
          <h1 className="text-5xl font-bold mb-4 bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent">
            Contract Generation Platform
          </h1>
          <h2 className="chat-title">Transforming Concepts into Professional Contracts</h2>
          {/* <h2 className="chat-title">I am your Ideation To POC remote assistant. Let's build your requirements document together!</h2> */}
        </div>
      )}
      {messages.length > 0 && (
        <div className="chat-scroll">
          <div className="chat-messages">
            <React.Fragment>
              {messages.length > 0 && (
                <div className="chat-bubble user">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{messages[0].content}</ReactMarkdown>
                </div>
              )}
              {loading && (
                <div className="chat-bubble assistant">
                  <div className="typing-animation">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                </div>
              )}
              {selectedTitle.length > 0 && (
                <div
                  className="chat-bubble assistant"
                  id="selectedTitle"
                  contentEditable
                  suppressContentEditableWarning
                  onBlur={(e) => {
                    if (e.target.textContent !== selectedTitle) {
                      handleContentUpdate(e, "title");
                    }
                  }}
                >
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{`### **${selectedTitle}**`}</ReactMarkdown>
                </div>
              )}
              {rephrasedIdea.length > 0 && (
                <div
                  className="chat-bubble assistant"
                  id="rephrasedIdea"
                  contentEditable
                  suppressContentEditableWarning
                  onBlur={(e) => {
                    if (e.target.textContent !== rephrasedIdea) {
                      handleContentUpdate(e, "idea");
                    }
                  }}
                >
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{rephrasedIdea}</ReactMarkdown>
                </div>
              )}


              {/* {titles.length > 0 && <SelectableList />} */}
              {/* initialChatStep === "show-sections" && */}

              {/* <div ref={messagesEndRef} /> */}

              {contractSections.length > 0 && (
                <div className="flex flex-col items-start justify-start">
                  <ContractSectionsDisplay />
                </div>
              )}
            </React.Fragment>
          </div>
        </div>
      )}

      <motion.div className="chat-input-box" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }}>
        <textarea
          placeholder={initialChatStep == "idea-submission" ? "What problem are you interested in solving?" : ""}
          value={input}
          onChange={(e) => {
            setInput(e.target.value);
            // Auto-adjust height based on content
            e.target.style.height = "auto";
            e.target.style.height = `${Math.min(Math.max(e.target.scrollHeight, 60), 150)}px`;
          }}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              handleSend();
            }
          }}
          className="chat-input"
          style={{
            resize: "none",
            minHeight: "60px",
            maxHeight: "150px",
            overflow: "auto",
          }}
        />
        <button onClick={handleSend} className="send-button">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="send-icon">
            <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 21l16.5-9L3.75 3v7.5l11.25 1.5-11.25 1.5V21z" />
          </svg>
        </button>
      </motion.div>
    </div>
  );
}
