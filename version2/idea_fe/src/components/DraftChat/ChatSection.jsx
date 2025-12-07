import React, { useEffect, useRef } from "react";
import { motion } from "framer-motion";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import "../InitialChat.css";
import { useChat } from "../../ChatContext";

export default function ChatSection() {
  const { input, setInput, handleDraftChat, draftMessages, loading, isReviewedSectionDraftActive } = useChat();
  const messagesEndRef = useRef(null);

  // Auto-scroll to bottom when messages change or loading state changes
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [draftMessages, loading]);

  useEffect(() => {
    console.log("this runs twise");
    handleDraftChat();
  }, []);

  // const handleContinueChat = ()=>{
  //   setInput(draftMessages[activeSection])
  //   setIsReviewedSectionDraftActive(false);
  // }

  return (
    <div className="flex flex-col h-full w-full pr-3">
      <div className="chat-scroll">
        <div className="chat-messages">
          <React.Fragment>
            {draftMessages.map((msg, i) => (
              <>
                <div key={i} className={`chat-bubble ${msg.role === "user" ? "user" : "assistant"}`}>
                  {msg?.reason && (
                    <span className="tooltip">
                      <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="none" stroke="purple" stroke-width="1.5" viewBox="0 0 24 24">
                        <circle cx="12" cy="12" r="10" />
                        <line x1="12" y1="8" x2="12" y2="8" stroke-linecap="round" />
                        <line x1="12" y1="12" x2="12" y2="16" stroke-linecap="round" />
                      </svg>

                      <span className="tooltip-content">{msg?.reason}</span>
                    </span>
                  )}
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content}</ReactMarkdown>
                </div>
              </>
            ))}
            {isReviewedSectionDraftActive && (
              <button className="startPocButton" onClick={() => handleDraftChat()}>
                Continue
              </button>
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
            {/* Invisible element for auto-scrolling */}
            <div ref={messagesEndRef} />
          </React.Fragment>
        </div>
      </div>

      <motion.div className="chat-input-box mx-2" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }}>
        <textarea
          placeholder={draftMessages.length > 0 ? "" : "Let's start by sharing your project idea or business concept here."}
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
              handleDraftChat();
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
        <button onClick={handleDraftChat} className="send-button">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="send-icon">
            <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 21l16.5-9L3.75 3v7.5l11.25 1.5-11.25 1.5V21z" />
          </svg>
        </button>
      </motion.div>
    </div>
  );
}
