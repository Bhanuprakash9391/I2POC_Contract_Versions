import React, { useEffect, useLayoutEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { useChat } from "../../ChatContext";

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
      // const match = line.match(/^(.+?):\s*(.+)$/);
      // if (match) {
      //   const [_, subHeading, subBody] = match;
      //   paragraphs.push(
      //     new Paragraph({
      //       children: [
      //         new TextRun({
      //           text: subHeading + ":",
      //           // bold: true,
      //           size: 26,
      //           font: "Calibri",
      //         }),
      //       ],
      //       spacing: { before: 100, after: 100, line: 276 },
      //     })
      //   );
      //   paragraphs.push(
      //     new Paragraph({
      //       children: [new TextRun({ text: subBody, size: 22, font: "Calibri" })],
      //       spacing: { after: 200, line: 276 },
      //     })
      //   );
      // } else {
      paragraphs.push(
        new Paragraph({
          children: [new TextRun({ text: line, size: 22, font: "Calibri" })],
          spacing: { after: 200, line: 276 },
        })
      );
      // }
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

const DynamicDocumentation = () => {
  const { drafts, setDrafts, contractSections, activeSection, isDraftingComplete, selectedTitle } = useChat();

  const [expandedSections, setExpandedSections] = useState({});
  const sectionRefs = useRef({});
  const contentRefs = useRef({});
  const containerRef = useRef(null);
  const [isSaved, setIsSaved] = useState(false);
  const [savedSessionId, setSavedSessionId] = useState(null);

  // Check if this idea has already been saved
  useEffect(() => {
    const savedIdeas = JSON.parse(localStorage.getItem('savedIdeas') || '{}');
    const currentIdeaKey = `${selectedTitle}_${Object.keys(drafts).length}`;
    if (savedIdeas[currentIdeaKey]) {
      setIsSaved(true);
      setSavedSessionId(savedIdeas[currentIdeaKey]);
    }
  }, [selectedTitle, drafts]);

  const toggleSection = (section) => {
    setExpandedSections((prev) => ({ [section]: !prev[section] }));
    // setExpandedSections((prev) => ({ [section]: !prev[section] }));
  };

  // Handle activeSection changes - expand the section and scroll to it
  useEffect(() => {
    if (activeSection) {
      setExpandedSections(() => ({ [activeSection]: true }));
    }
  }, [activeSection]);

  // Scroll to active section when it becomes expanded or when drafts update
  useLayoutEffect(() => {
    if (activeSection && expandedSections[activeSection] && contentRefs.current[activeSection] && containerRef.current) {
      const contentEl = contentRefs.current[activeSection];
      const containerEl = containerRef.current;

      // Get the content element's position relative to the container
      const contentTop = contentEl.offsetTop;
      const containerTop = containerEl.offsetTop;

      // Calculate the scroll position to show the content at the top
      // We subtract a small offset to give some breathing room
      const scrollOffset = 20;
      const targetScrollTop = contentTop - containerTop - scrollOffset;

      // Add a small delay to ensure DOM is updated
      setTimeout(() => {
        containerEl.scrollTo({
          top: targetScrollTop,
          behavior: "smooth",
        });
      }, 150);
    }
  }, [activeSection, expandedSections, drafts]);

  const Arrow = ({ expanded }) => (
    <div style={{ transform: expanded ? "rotate(90deg)" : "rotate(0deg)", transition: "transform 0.2s ease" }}>
      <div
        style={{
          width: 0,
          height: 0,
          borderLeft: "6px solid #9CA3AF",
          borderTop: "4px solid transparent",
          borderBottom: "4px solid transparent",
        }}
      ></div>
    </div>
  );

  return (
    <div ref={containerRef} className="pl-3 w-full" style={{ maxWidth: "1024px", margin: "0 auto", height: "75vh", overflowY: "auto" }}>
      {isDraftingComplete && (
        <div>
          <h2 style={{ fontSize: "20px", fontWeight: "bold", color: "#1F2937", marginBottom: "16px" }}>
            Contract Document - Ready for Review
          </h2>
        </div>
      )}

      <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
        {contractSections.map((section, index) => (
          <div
            key={index}
            ref={(el) => (sectionRefs.current[section?.section_heading] = el)}
            style={{ borderRadius: "16px", boxShadow: "0 1px 3px rgba(0, 0, 0, 0.1)", border: "1px solid #E5E7EB", overflow: "hidden" }}
          >
            <div style={{ padding: "16px", cursor: "pointer", borderBottom: "1px solid #F3F4F6" }} onClick={() => toggleSection(section?.section_heading)}>
              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <div className="flex flex-col items-start text-left">
                  <h2 style={{ fontSize: "18px", fontWeight: "600", color: "#1F2937" }}>{section?.section_heading}</h2>
                  <div className="text-left" style={{ fontSize: "12px", fontWeight: "600", color: "#1F2937" }}>
                    {section?.section_purpose}
                  </div>
                </div>
                {/* <Arrow expanded={expandedSections[section?.section_heading]} /> */}
                {expandedSections[section?.section_heading] ? (
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="purple">
                    <path d="M5 8l7 11 7-11z" />
                  </svg>
                ) : (
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="purple">
                    <path d="M8 5v14l11-7z" />
                  </svg>
                )}
              </div>
            </div>

            {expandedSections[section?.section_heading] && (
              <div ref={(el) => (contentRefs.current[section?.section_heading] = el)} style={{ padding: "24px" }}>
                <div style={{ position: "relative" }}>
                  {!expandedSections[`${section?.section_heading}-edit`] ? (
                    <div className="flex flex-col items-end">
                      <div className="text-left w-full">
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>{drafts[section?.section_heading]}</ReactMarkdown>
                      </div>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setExpandedSections((prev) => ({ ...prev, [`${section?.section_heading}-edit`]: true }));
                        }}
                        style={{
                          cursor: "pointer",
                          fontSize: "14px",
                          background: "linear-gradient(to right, #c59c51, #eab308)",
                          border: "none",
                          padding: "8px",
                          borderRadius: "9999px",
                          color: "white",
                        }}
                      >
                        {/* ✏️ Edit */}
                        <svg
                          xmlns="http://www.w3.org/2000/svg"
                          width="16"
                          height="16"
                          fill="none"
                          stroke="white"
                          strokeWidth="2"
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          viewBox="0 0 24 24"
                        >
                          <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
                          <path d="m18.5 2.5 3 3L12 15l-4 1 1-4Z" />
                        </svg>
                      </button>
                    </div>
                  ) : (
                    <div className="flex flex-col items-end">
                      <textarea
                        value={drafts[section?.section_heading] || ""}
                        onChange={(e) => setDrafts((prev) => ({ ...prev, [section?.section_heading]: e.target.value }))}
                        style={{ width: "100%", minHeight: "300px", padding: "8px", border: "1px solid #E5E7EB", borderRadius: "4px", resize: "vertical" }}
                      />
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setExpandedSections((prev) => ({ ...prev, [`${section?.section_heading}-edit`]: false }));
                        }}
                        style={{
                          cursor: "pointer",
                          fontSize: "14px",
                          background: "linear-gradient(to right, #c59c51, #eab308)",
                          border: "none",
                          padding: "8px",
                          borderRadius: "9999px",
                          color: "white",
                          marginTop: "10px",
                        }}
                      >
                        {/* ✅ Save */}
                        <svg
                          xmlns="http://www.w3.org/2000/svg"
                          width="16"
                          height="16"
                          fill="none"
                          stroke="white"
                          strokeWidth="2"
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          viewBox="0 0 24 24"
                        >
                          <path d="M20 6L9 17l-5-5" />
                        </svg>
                      </button>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Action Buttons at Bottom */}
      {isDraftingComplete && (
        <div style={{ marginTop: "32px", padding: "16px", borderTop: "1px solid #E5E7EB" }}>
          <div style={{ display: "flex", justifyContent: "center", gap: "16px" }}>
            {!isSaved ? (
              <button
                style={{
                  cursor: "pointer",
                  fontSize: "14px",
                  background: "linear-gradient(to right, #10B981, #059669)",
                  border: "none",
                  padding: "12px 24px",
                  borderRadius: "8px",
                  color: "white",
                  fontWeight: "600",
                }}
                onClick={async () => {
                  try {
                    // Create the complete document from all drafts
                    const completeDocument = Object.entries(drafts)
                      .map(([section, content]) => `## ${section}\n\n${content}`)
                      .join('\n\n');
                    
                    // Submit the idea with complete document and all drafts
                    const response = await fetch('/apcontract/contracts', {
                      method: 'POST',
                      headers: {
                        'Content-Type': 'application/json',
                      },
                      body: JSON.stringify({
                        title: selectedTitle || 'Untitled Idea',
                        idea: completeDocument,
                        drafts: drafts, // Save the actual draft content - use 'drafts' not 'all_drafts'
                        status: 'submitted',
                        metadata: {
                          is_poc_document: true,
                          sections_count: Object.keys(drafts).length,
                          created_at: new Date().toISOString(),
                          submitted_by: 'User',
                          department: 'General',
                          summary_type: 'complete_poc_document'
                        }
                      })
                    });
                    
                    if (response.ok) {
                      const result = await response.json();
                      setIsSaved(true); // Hide the button after successful save
                      setSavedSessionId(result.session_id);
                      
                      // Store in localStorage to prevent duplicates
                      const savedIdeas = JSON.parse(localStorage.getItem('savedIdeas') || '{}');
                      const currentIdeaKey = `${selectedTitle}_${Object.keys(drafts).length}`;
                      savedIdeas[currentIdeaKey] = result.session_id;
                      localStorage.setItem('savedIdeas', JSON.stringify(savedIdeas));
                      
                      alert('Contract saved successfully! It will now appear in the Contract Catalog for review.');
                      console.log('Contract saved with session ID:', result.session_id);
                    } else {
                      const errorText = await response.text();
                      console.error('Save failed:', errorText);
                      alert('Failed to save idea. Please check if the backend server is running.');
                    }
                  } catch (error) {
                    console.error('Error saving idea:', error);
                    alert('Error saving idea. Please check if the backend server is running at http://localhost:8000');
                  }
                }}
              >
                Save Contract to Catalogue
              </button>
            ) : (
              <div style={{
                padding: "12px 24px",
                borderRadius: "8px",
                background: "#E5E7EB",
                color: "#6B7280",
                fontWeight: "600",
                fontSize: "14px",
                textAlign: "center"
              }}>
              ✅ Contract Saved to Catalog
              </div>
            )}
            <button
              style={{
                cursor: "pointer",
                fontSize: "14px",
                background: "linear-gradient(to right, #c59c51, #eab308)",
                border: "none",
                padding: "12px 24px",
                borderRadius: "8px",
                color: "white",
                fontWeight: "600",
              }}
              onClick={() => generateDraftsDocx(drafts, selectedTitle)}
            >
              Download
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default DynamicDocumentation;
