import React, { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import { useChat } from "../../ChatContext";
// import { createWordDocFromMarkdown } from "../../utils/downloadDocx";

// const generateDraftsDocx = async (drafts) => {
//   const { Document, Packer, Paragraph, TextRun } = await import("docx");

//   const createFormattedSection = (title, content) => {
//     const paragraphs = [];

//     // Main Section Title
//     paragraphs.push(
//       new Paragraph({
//         children: [
//           new TextRun({
//             text: title,
//             bold: true,
//             color: "2F5496",
//             size: 32, // 16pt
//             font: "Calibri",
//           }),
//         ],
//         spacing: {
//           after: 200, // 10pt
//         },
//       })
//     );

//     // Detect Subsections (e.g., "Background:", "Goals:")
//     const lines = content.split(/\n+/).filter(Boolean);

//     for (const line of lines) {
//       const match = line.match(/^(.+?):\s*(.+)$/);
//       if (match) {
//         const [_, subTitle, subBody] = match;

//         // Subsection Heading
//         paragraphs.push(
//           new Paragraph({
//             children: [
//               new TextRun({
//                 text: subTitle + ":",
//                 bold: true,
//                 size: 26, // ~13pt
//                 font: "Calibri",
//               }),
//             ],
//             spacing: {
//               after: 100,
//               before: 100,
//             },
//           })
//         );

//         // Subsection Body
//         paragraphs.push(
//           new Paragraph({
//             children: [
//               new TextRun({
//                 text: subBody,
//                 size: 24,
//                 font: "Calibri",
//                 characterSpacing: 20,
//               }),
//             ],
//             spacing: {
//               after: 200,
//             },
//           })
//         );
//       } else {
//         // Regular paragraph
//         paragraphs.push(
//           new Paragraph({
//             children: [
//               new TextRun({
//                 text: line,
//                 size: 24,
//                 font: "Calibri",
//                 characterSpacing: 20,
//               }),
//             ],
//             spacing: {
//               after: 200,
//             },
//           })
//         );
//       }
//     }

//     return paragraphs;
//   };

//   const doc = new Document({
//     sections: [
//       {
//         properties: {},
//         children: Object.entries(drafts).flatMap(([title, content]) => createFormattedSection(title, content)),
//       },
//     ],
//   });

//   const blob = await Packer.toBlob(doc);
//   const url = window.URL.createObjectURL(blob);
//   const link = document.createElement("a");
//   link.href = url;
//   link.download = "drafts.docx";
//   document.body.appendChild(link);
//   link.click();
//   document.body.removeChild(link);
// };

const generateDraftsDocx = async (drafts) => {
  const { Document, Packer, Paragraph, TextRun } = await import("docx");

  const createFormattedSection = (title, content) => {
    const paragraphs = [];

    // Section Title
    paragraphs.push(
      new Paragraph({
        children: [
          new TextRun({
            text: title,
            bold: true,
            color: "2F5496", // professional blue
            size: 32, // 16pt
            font: "Calibri",
          }),
        ],
        spacing: {
          after: 200, // ~10pt after heading
        },
      })
    );

    // Split content into logical blocks
    const lines = content.split(/\n+/).filter(Boolean);
    for (const line of lines) {
      const match = line.match(/^(.+?):\s*(.+)$/);
      if (match) {
        const [_, subHeading, subBody] = match;

        // Subheading
        paragraphs.push(
          new Paragraph({
            children: [
              new TextRun({
                text: subHeading + ":",
                bold: true,
                size: 26, // ~13pt
                font: "Calibri",
              }),
            ],
            spacing: {
              before: 100,
              after: 100,
              line: 276, // 1.15 line spacing
            },
          })
        );

        // Subsection Body
        paragraphs.push(
          new Paragraph({
            children: [
              new TextRun({
                text: subBody,
                size: 22, // 11pt
                font: "Calibri",
              }),
            ],
            spacing: {
              after: 200,
              line: 276,
            },
          })
        );
      } else {
        // Regular paragraph
        paragraphs.push(
          new Paragraph({
            children: [
              new TextRun({
                text: line,
                size: 22,
                font: "Calibri",
              }),
            ],
            spacing: {
              after: 200,
              line: 276,
            },
          })
        );
      }
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
  link.href = url;
  link.download = "drafts.docx";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};

const DynamicDocumentation = () => {
  const { drafts, setDrafts, contractSections, activeSection } = useChat();
  const [expandedSections, setExpandedSections] = useState({});

  const toggleSection = (section) => {
    setExpandedSections((prev) => ({
      // ...prev,
      [section]: !prev[section],
    }));
  };

  useEffect(() => {
    toggleSection(activeSection);
  }, [activeSection]);

  // Custom arrow component using CSS
  const Arrow = ({ expanded }) => (
    <div
      style={{
        width: "20px",
        height: "20px",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        transform: expanded ? "rotate(90deg)" : "rotate(0deg)",
        transition: "transform 0.2s ease",
      }}
    >
      <div
        style={{
          width: "0",
          height: "0",
          borderLeft: "6px solid #9CA3AF",
          borderTop: "4px solid transparent",
          borderBottom: "4px solid transparent",
        }}
      ></div>
    </div>
  );

  return (
    <div
      style={{
        maxWidth: "1024px",
        margin: "0 auto",
        // padding: "10px 24px",
        // backgroundColor: "transparent",
        // minHeight: "100vh",
        height: "75vh",
        overflowY: "auto",
      }}
      className="pl-3"
    >
      <div style={{ marginBottom: "32px" }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "end", marginBottom: "8px", marginTop: "10px" }}>
          <button
            style={{
              cursor: "pointer",
              fontSize: "14px",
              background: "linear-gradient(to right, #c59c51, #eab308)",
              border: "none",
              padding: "8px",
              borderRadius: "9999px",
              color: "white",
            }}
            onClick={() => generateDraftsDocx(drafts)}
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
              <path d="M.5 9.9a.5.5 0 0 1 .5.5v2.5a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-2.5a.5.5 0 0 1 1 0v2.5a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2v-2.5a.5.5 0 0 1 .5-.5z" />
              <path d="M7.646 11.854a.5.5 0 0 0 .708 0l3-3a.5.5 0 0 0-.708-.708L8.5 10.293V1.5a.5.5 0 0 0-1 0v8.793L5.354 8.146a.5.5 0 1 0-.708.708l3 3z" />
            </svg>
            {/* Download .docx */}
          </button>
        </div>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
        {/* {Object.entries(drafts).map(([key, value]) => ( */}
        {contractSections.map((section, index) => (
          <div
            key={index}
            style={{
              borderRadius: "16px",
              boxShadow: "0 1px 3px rgba(0, 0, 0, 0.1)",
              border: "1px solid #E5E7EB",
              overflow: "hidden",
            }}
          >
            <div
              style={{
                padding: "16px",
                cursor: "pointer",
                borderBottom: "1px solid #F3F4F6",
                transition: "background-color 0.2s ease",
              }}
              onClick={() => toggleSection(section?.section_heading)}
              // onMouseEnter={(e) => (e.target.style.backgroundColor = "white")}
              // onMouseLeave={(e) => (e.target.style.backgroundColor = "white")}
            >
              <div
                style={{
                  display: "flex",
                  alignItems: "start",
                  justifyContent: "space-between",
                }}
              >
                <div className="flex flex-col items-start justify-center text-left">
                  <h2
                    style={{
                      fontSize: "18px",
                      fontWeight: "600",
                      color: "#1F2937",
                    }}
                  >
                    {section?.section_heading}
                  </h2>
                  <div
                    style={{
                      fontSize: "12px",
                      fontWeight: "600",
                      color: "#1F2937",
                    }}
                  >
                    {section?.section_purpose}
                  </div>
                </div>
                {/* <Arrow expanded={expandedSections[section?.section_heading]} /> */}
                {expandedSections[section?.section_heading] ? (
                  <svg xmlns="http://www.w3.org/2000/svg" width="9" height="9" viewBox="0 0 24 24" fill="#9CA3AF">
                    <path d="M8 5v14l11-7z" />
                  </svg>
                ) : (
                  <svg xmlns="http://www.w3.org/2000/svg" width="9" height="9" viewBox="0 0 24 24" fill="#9CA3AF">
                    <path d="M5 8l7 11 7-11z" />
                  </svg>
                )}
              </div>
            </div>

            {expandedSections[section?.section_heading] && (
              <div
                style={{
                  padding: "24px",
                  backgroundColor: "transparent",
                }}
              >
                <div style={{ position: "relative" }}>
                  {!expandedSections[`${section?.section_heading}-edit`] ? (
                    <div className="flex flex-col items-end">
                      {/* <div>{formatContent(drafts[section?.section_heading])}</div> */}
                      <div className="text-left w-full">
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>{drafts[section?.section_heading]}</ReactMarkdown>
                      </div>

                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setExpandedSections((prev) => ({
                            ...prev,
                            [`${section?.section_heading}-edit`]: true,
                          }));
                        }}
                        style={{
                          cursor: "pointer",
                          fontSize: "14px",
                          background: "linear-gradient(to right, #c59c51, #eab308)",
                          border: "none",
                          padding: "8px",
                          borderRadius: "9999px",
                          color: "white",
                          top: "0",
                          right: "0",
                        }}
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="#6B7280" viewBox="0 0 16 16">
                          <path d="M12.854.146a.5.5 0 0 0-.707 0L10.5 1.793 14.207 5.5l1.647-1.646a.5.5 0 0 0 0-.708l-3-3zm.646 6.061L9.793 2.5 3.293 9H3.5a.5.5 0 0 1 .5.5v.5h.5a.5.5 0 0 1 .5.5v.5h.5a.5.5 0 0 1 .5.5v.5h.5a.5.5 0 0 1 .5.5v.207l6.5-6.5zm-7.468 7.468A.5.5 0 0 1 6 13.5V13h-.5a.5.5 0 0 1-.5-.5V12h-.5a.5.5 0 0 1-.5-.5V11h-.5a.5.5 0 0 1-.5-.5V10h-.5a.499.499 0 0 1-.175-.032l-.179.178a.5.5 0 0 0-.11.168l-2 5a.5.5 0 0 0 .65.65l5-2a.5.5 0 0 0 .168-.11l.178-.178z" />
                        </svg>
                      </button>
                    </div>
                  ) : (
                    <div className="flex flex-col items-end justify-end">
                      <textarea
                        value={drafts[section?.section_heading] || ""}
                        onChange={(e) => {
                          console.log("e.target.value", e.target.value);
                          setDrafts((prev) => ({
                            ...prev,
                            [section?.section_heading]: e.target.value,
                          }));
                        }}
                        style={{
                          width: "100%",
                          minHeight: "300px",
                          padding: "8px",
                          border: "1px solid #E5E7EB",
                          borderRadius: "4px",
                          resize: "vertical",
                        }}
                      />
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setExpandedSections((prev) => ({
                            ...prev,
                            [`${section?.section_heading}-edit`]: false,
                          }));
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
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="#6B7280" viewBox="0 0 16 16">
                          <path d="M13.854 3.646a.5.5 0 0 1 0 .708l-7 7a.5.5 0 0 1-.708 0l-3.5-3.5a.5.5 0 1 1 .708-.708L6.5 10.293l6.646-6.647a.5.5 0 0 1 .708 0z" />
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
    </div>
  );
};

export default DynamicDocumentation;
