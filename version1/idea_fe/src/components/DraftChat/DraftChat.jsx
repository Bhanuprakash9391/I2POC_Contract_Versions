import { useChat } from "../../ChatContext";
import ProgressIndicator from "./ProgressIndicator";
// import DraftSection from "./DraftSectionO";
import DraftSection from "./DraftSection";
import ChatSection from "./ChatSection";
import "../InitialChat.css";
import { useState } from "react";

export default function DraftChat() {
  const { initialChatStep, contractSections, selectedTitle } = useChat();
  // const [isDraftVisible, setIsDraftVisible] = useState(true);
  const [isChatVisible, setIsChatVisible] = useState(true);

  // Only render this component when initialChatStep is "done"
  if (initialChatStep !== "done") {
    return null;
  }

  return (
    <div className="draft-container flex flex-col h-screen bg-gradient-to-br from-indigo-50 to-purple-50">
      {/* Progress Indicator */}
      <h1 className="text-4xl font-bold text-purple-800 my-4">{selectedTitle}</h1>
      <ProgressIndicator steps={contractSections} title={selectedTitle} />
      <div className="border border-b-0 mb-2 border-purple-100"></div>
      <div className="flex items-center justify-start position-relative h-0 ">
        <button
          style={{ position: "fixed", top: "105px" }}
          onClick={() => setIsChatVisible(!isChatVisible)}
          className="p-1 bg-purple-50 hover:bg-purple-100 rounded-full send-button z-10 position-sticky top-30"
        >
          {isChatVisible ? (
            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          ) : (
            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          )}
        </button>
      </div>
      <div className="flex flex-1 overflow-hidden">
        {/* Left Chat Section */}
        {isChatVisible && (
          <div className={`${isChatVisible ? "w-1/2" : "w-0"} border-r border-purple-100`}>
            <ChatSection />
          </div>
        )}

        {/* Right Draft Section */}
        <div
          className={`transition-all duration-200 ${isChatVisible ? "w-1/2" : "w-full"} `}
          style={{
            resize: "horizontal",
            overflow: "auto",
            minWidth: "300px",
            // maxWidth: "1000px",
          }}
        >
          <DraftSection />
        </div>
      </div>
    </div>
  );
}
