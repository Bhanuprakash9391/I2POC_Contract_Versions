// Function to convert markdown to DOCX and download with professional contract formatting
import { saveAs } from "file-saver";
import jsPDF from "jspdf";
// Requires: npm install docx file-saver jspdf
// Using dynamic imports to avoid static/dynamic import conflicts

async function createWordDoc(content, filename = "contract_document.docx") {
  // Dynamically import docx to avoid static/dynamic import conflicts
  const { Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType, BorderStyle, Table, TableCell, TableRow, WidthType } = await import("docx");
  
  const lines = content.split("\n");
  const paragraphs = [];

  // Add professional contract header
  paragraphs.push(
    new Paragraph({
      children: [
        new TextRun({
          text: "CONTRACT AGREEMENT",
          bold: true,
          size: 36, // 18pt
          color: "2F5496", // Professional blue
          allCaps: true,
        }),
      ],
      alignment: AlignmentType.CENTER,
      spacing: { before: 400, after: 300 },
      border: {
        bottom: {
          style: BorderStyle.DOUBLE,
          size: 12,
          color: "2F5496",
        },
      },
    })
  );

  // Add contract sections with professional formatting
  let currentSection = null;
  let inSubsection = false;

  lines.forEach((line) => {
    const trimmedLine = line.trim();
    
    // Skip empty lines but add minimal spacing
    if (trimmedLine === "") {
      paragraphs.push(new Paragraph({ text: "", spacing: { after: 80 } }));
      return;
    }

    // Handle section headers (## Section Name)
    if (trimmedLine.startsWith("## ")) {
      currentSection = trimmedLine.replace("## ", "");
      inSubsection = false;
      
      paragraphs.push(
        new Paragraph({
          children: [
            new TextRun({
              text: currentSection.toUpperCase(),
              bold: true,
              size: 28, // 14pt
              color: "2F5496",
              allCaps: true,
            }),
          ],
          heading: HeadingLevel.HEADING_2,
          spacing: { before: 400, after: 200 },
          border: {
            bottom: {
              style: BorderStyle.SINGLE,
              size: 4,
              color: "D0D0D0",
            },
          },
        })
      );
    }
    // Handle subsection headers (### Subsection Name)
    else if (trimmedLine.startsWith("### ")) {
      const subsectionName = trimmedLine.replace("### ", "");
      inSubsection = true;
      
      paragraphs.push(
        new Paragraph({
          children: [
            new TextRun({
              text: subsectionName,
              bold: true,
              size: 24, // 12pt
              color: "4472C4",
            }),
          ],
          heading: HeadingLevel.HEADING_3,
          spacing: { before: 300, after: 150 },
          indent: { left: 360 }, // 0.25 inch indent
        })
      );
    }
    // Handle numbered clauses (1., 2., etc.)
    else if (trimmedLine.match(/^\d+\.\s+/)) {
      const clauseText = trimmedLine.replace(/^\d+\.\s+/, "");
      
      paragraphs.push(
        new Paragraph({
          children: [
            new TextRun({
              text: trimmedLine.match(/^\d+\./)[0],
              bold: true,
              size: 22, // 11pt
              color: "2F5496",
            }),
            new TextRun({
              text: " " + clauseText,
              size: 22, // 11pt
            }),
          ],
          spacing: { before: 150, after: 120 },
          indent: { left: 720, hanging: 360 }, // 0.5 inch indent with hanging
        })
      );
    }
    // Handle sub-clauses (a., b., etc.)
    else if (trimmedLine.match(/^[a-z]\)\s+/)) {
      const subclauseText = trimmedLine.replace(/^[a-z]\)\s+/, "");
      
      paragraphs.push(
        new Paragraph({
          children: [
            new TextRun({
              text: trimmedLine.match(/^[a-z]\)/)[0],
              bold: true,
              size: 20, // 10pt
              color: "4472C4",
            }),
            new TextRun({
              text: " " + subclauseText,
              size: 20, // 10pt
            }),
          ],
          spacing: { before: 100, after: 80 },
          indent: { left: 1080, hanging: 360 }, // 0.75 inch indent with hanging
        })
      );
    }
    // Handle bullet points
    else if (trimmedLine.startsWith("* ") || trimmedLine.startsWith("- ")) {
      const bulletText = trimmedLine.substring(2);
      
      paragraphs.push(
        new Paragraph({
          children: [
            new TextRun({
              text: "• ",
              bold: true,
              size: 20, // 10pt
            }),
            new TextRun({
              text: bulletText,
              size: 20, // 10pt
            }),
          ],
          spacing: { before: 80, after: 60 },
          indent: { left: 1080, hanging: 360 }, // 0.75 inch indent with hanging
        })
      );
    }
    // Handle bold text (for emphasis)
    else if (trimmedLine.includes("**")) {
      const parts = trimmedLine.split("**");
      const children = [];
      
      parts.forEach((part, index) => {
        if (part.trim()) {
          children.push(
            new TextRun({
              text: part,
              bold: index % 2 === 1, // Every second part is bold
              size: 22, // 11pt
              color: index % 2 === 1 ? "2F5496" : "000000",
            })
          );
        }
      });
      
      paragraphs.push(
        new Paragraph({
          children: children,
          spacing: { before: 120, after: 100 },
          alignment: AlignmentType.JUSTIFIED,
        })
      );
    }
    // Regular paragraph text
    else {
      paragraphs.push(
        new Paragraph({
          children: [
            new TextRun({
              text: trimmedLine,
              size: 22, // 11pt
            }),
          ],
          spacing: { before: 100, after: 100 },
          alignment: AlignmentType.JUSTIFIED,
          indent: inSubsection ? { left: 720 } : { firstLine: 360 }, // 0.5 inch indent for subsections
        })
      );
    }
  });

  // Add signature section at the end
  paragraphs.push(
    new Paragraph({
      children: [
        new TextRun({
          text: "",
          size: 22,
        }),
      ],
      spacing: { before: 400, after: 200 },
    })
  );

  // Add signature lines
  const signatureTable = new Table({
    width: {
      size: 100,
      type: WidthType.PERCENTAGE,
    },
    rows: [
      new TableRow({
        children: [
          new TableCell({
            children: [
              new Paragraph({
                children: [
                  new TextRun({
                    text: "_________________________",
                    size: 22,
                  }),
                ],
                alignment: AlignmentType.CENTER,
              }),
              new Paragraph({
                children: [
                  new TextRun({
                    text: "Party A Signature",
                    size: 18,
                    bold: true,
                  }),
                ],
                alignment: AlignmentType.CENTER,
                spacing: { before: 80 },
              }),
            ],
            margins: { top: 200, bottom: 200, left: 200, right: 200 },
          }),
          new TableCell({
            children: [
              new Paragraph({
                children: [
                  new TextRun({
                    text: "_________________________",
                    size: 22,
                  }),
                ],
                alignment: AlignmentType.CENTER,
              }),
              new Paragraph({
                children: [
                  new TextRun({
                    text: "Party B Signature",
                    size: 18,
                    bold: true,
                  }),
                ],
                alignment: AlignmentType.CENTER,
                spacing: { before: 80 },
              }),
            ],
            margins: { top: 200, bottom: 200, left: 200, right: 200 },
          }),
        ],
      }),
    ],
  });

  paragraphs.push(signatureTable);

  // Create professional document
  const doc = new Document({
    styles: {
      paragraphStyles: [
        {
          id: "Normal",
          name: "Normal",
          basedOn: "Normal",
          next: "Normal",
          run: {
            size: 22, // 11pt
            font: "Calibri",
          },
          paragraph: {
            spacing: { line: 276 }, // 1.15 line spacing
            alignment: AlignmentType.JUSTIFIED,
          },
        },
        {
          id: "Heading1",
          name: "Heading 1",
          basedOn: "Normal",
          next: "Normal",
          run: {
            size: 32, // 16pt
            bold: true,
            color: "2F5496",
            font: "Calibri",
          },
          paragraph: {
            spacing: { before: 400, after: 200 },
            alignment: AlignmentType.CENTER,
          },
        },
        {
          id: "Heading2",
          name: "Heading 2",
          basedOn: "Normal",
          next: "Normal",
          run: {
            size: 28, // 14pt
            bold: true,
            color: "2F5496",
            font: "Calibri",
            allCaps: true,
          },
          paragraph: {
            spacing: { before: 400, after: 200 },
          },
        },
      ],
    },
    sections: [
      {
        properties: {
          page: {
            margin: {
              top: 1440, // 1 inch
              right: 1440, // 1 inch
              bottom: 1440, // 1 inch
              left: 1440, // 1 inch
            },
          },
        },
        children: paragraphs,
      },
    ],
  });

  // Generate and download
  Packer.toBlob(doc).then((blob) => {
    saveAs(blob, filename);
  });
}

// function to create PDF from text content
function createPDF(content, filename = "document.pdf") {
  const doc = new jsPDF();
  const pageWidth = doc.internal.pageSize.getWidth();
  const pageHeight = doc.internal.pageSize.getHeight();
  const margin = 20;
  const maxWidth = pageWidth - 2 * margin;
  let yPosition = margin;

  const lines = content.split("\n");

  lines.forEach((line) => {
    // Skip empty lines but add some spacing
    if (line.trim() === "") {
      yPosition += 5;
      return;
    }

    // Check if we need a new page
    if (yPosition > pageHeight - margin) {
      doc.addPage();
      yPosition = margin;
    }

    // Handle different line types
    if (line.match(/^\d+\./)) {
      // Numbered items (1., 2., etc.)
      doc.setFontSize(12);
      doc.setFont("helvetica", "bold");
      const wrappedText = doc.splitTextToSize(line, maxWidth);
      wrappedText.forEach((textLine, index) => {
        if (yPosition > pageHeight - margin) {
          doc.addPage();
          yPosition = margin;
        }
        doc.text(textLine, margin + (index > 0 ? 15 : 0), yPosition);
        yPosition += 6;
      });
      yPosition += 3;
    } else if (line.includes("**") && line.includes(":**")) {
      // Bold items with colons (like **Product Development:**)
      doc.setFontSize(11);
      doc.setFont("helvetica", "bold");
      // Remove ** from text
      const cleanLine = line.replace(/\*\*/g, "");
      const wrappedText = doc.splitTextToSize(cleanLine, maxWidth - 20);
      wrappedText.forEach((textLine) => {
        if (yPosition > pageHeight - margin) {
          doc.addPage();
          yPosition = margin;
        }
        doc.text(textLine, margin + 20, yPosition);
        yPosition += 6;
      });
      yPosition += 2;
    } else if (line.trim().startsWith("*")) {
      // Bullet points
      doc.setFontSize(10);
      doc.setFont("helvetica", "normal");
      const bulletText = "• " + line.trim().substring(1).trim();
      // Remove ** from text
      const cleanText = bulletText.replace(/\*\*/g, "");
      const wrappedText = doc.splitTextToSize(cleanText, maxWidth - 30);
      wrappedText.forEach((textLine, index) => {
        if (yPosition > pageHeight - margin) {
          doc.addPage();
          yPosition = margin;
        }
        doc.text(textLine, margin + 30 + (index > 0 ? 10 : 0), yPosition);
        yPosition += 5;
      });
      yPosition += 2;
    } else if (line.includes("Scope (")) {
      // Section headers
      doc.setFontSize(14);
      doc.setFont("helvetica", "bold");
      doc.text(line, margin, yPosition);
      yPosition += 10;
    } else {
      // Regular text
      doc.setFontSize(12);
      doc.setFont("helvetica", "normal");
      const wrappedText = doc.splitTextToSize(line, maxWidth);
      wrappedText.forEach((textLine) => {
        if (yPosition > pageHeight - margin) {
          doc.addPage();
          yPosition = margin;
        }
        doc.text(textLine, margin, yPosition);
        yPosition += 6;
      });
      yPosition += 4;
    }
  });

  doc.save(filename);
}

async function createWordDocFromMarkdown(content, filename = "document.docx") {
  // Dynamically import docx to avoid static/dynamic import conflicts
  const { Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType, BorderStyle } = await import("docx");
  
  const lines = content.split("\n");
  const paragraphs = [];

  lines.forEach((line, index) => {
    const trimmedLine = line.trim();

    // Skip empty lines but add spacing
    if (trimmedLine === "") {
      paragraphs.push(
        new Paragraph({
          text: "",
          spacing: { after: 100 },
        })
      );
      return;
    }

    // Handle different markdown elements
    if (isMainHeading(trimmedLine)) {
      // Main headings (# or ###)
      const headingText = trimmedLine.replace(/^#{1,6}\s*/, "");
      const level = getHeadingLevel(trimmedLine);

      paragraphs.push(
        new Paragraph({
          children: [
            new TextRun({
              text: headingText,
              bold: true,
              size: getHeadingFontSize(level),
              color: "2F5496", // Professional blue color
            }),
          ],
          heading: level,
          spacing: {
            before: level === HeadingLevel.HEADING_1 ? 400 : 300,
            after: 200,
          },
          border:
            level === HeadingLevel.HEADING_1
              ? {
                  bottom: {
                    style: BorderStyle.SINGLE,
                    size: 6,
                    color: "2F5496",
                  },
                }
              : undefined,
        })
      );
    } else if (isSubHeading(trimmedLine)) {
      // Sub-headings (#### or numbers like 1.1, 2.1, etc.)
      const headingText = trimmedLine.replace(/^#+\s*|\d+\.\d*\s*/, "");

      paragraphs.push(
        new Paragraph({
          children: [
            new TextRun({
              text: headingText,
              bold: true,
              size: 26, // 13pt
              color: "4472C4",
            }),
          ],
          heading: HeadingLevel.HEADING_3,
          spacing: { before: 240, after: 120 },
        })
      );
    } else if (isBulletPoint(trimmedLine)) {
      // Bullet points (starting with - or *)
      const bulletText = trimmedLine.replace(/^[-*]\s*/, "");
      const processedRuns = processInlineFormatting(bulletText);

      paragraphs.push(
        new Paragraph({
          children: [new TextRun({ text: "• " }), ...processedRuns],
          indent: { left: 720 }, // 0.5 inch indent
          spacing: { after: 100 },
          bullet: { level: 0 },
        })
      );
    } else if (isNumberedList(trimmedLine)) {
      // Numbered lists (1., 2., etc.)
      const listText = trimmedLine.replace(/^\d+\.\s*/, "");
      const processedRuns = processInlineFormatting(listText);

      paragraphs.push(
        new Paragraph({
          children: processedRuns,
          numbering: {
            reference: "default-numbering",
            level: 0,
          },
          indent: { left: 720 },
          spacing: { after: 100 },
        })
      );
    } else if (isBoldStatement(trimmedLine)) {
      // Bold statements (text with ** or ending with :)
      const processedRuns = processInlineFormatting(trimmedLine);

      paragraphs.push(
        new Paragraph({
          children: processedRuns,
          spacing: { after: 120 },
          indent: { left: 360 }, // Small indent for emphasis
        })
      );
    } else {
      // Regular paragraph text
      const processedRuns = processInlineFormatting(trimmedLine);

      paragraphs.push(
        new Paragraph({
          children: processedRuns,
          spacing: { after: 120 },
          alignment: AlignmentType.JUSTIFIED,
        })
      );
    }
  });

  // Create document with proper styling
  const doc = new Document({
    styles: {
      default: {
        heading1: {
          run: {
            size: 32,
            bold: true,
            color: "2F5496",
          },
          paragraph: {
            spacing: { after: 240, before: 400 },
          },
        },
        heading2: {
          run: {
            size: 28,
            bold: true,
            color: "2F5496",
          },
          paragraph: {
            spacing: { after: 200, before: 300 },
          },
        },
        heading3: {
          run: {
            size: 26,
            bold: true,
            color: "4472C4",
          },
          paragraph: {
            spacing: { after: 120, before: 240 },
          },
        },
      },
    },
    numbering: {
      config: [
        {
          reference: "default-numbering",
          levels: [
            {
              level: 0,
              format: "decimal",
              text: "%1.",
              alignment: AlignmentType.START,
              style: {
                paragraph: {
                  indent: { left: 720, hanging: 260 },
                },
              },
            },
          ],
        },
      ],
    },
    sections: [
      {
        properties: {
          page: {
            margin: {
              top: 1440, // 1 inch
              right: 1440, // 1 inch
              bottom: 1440, // 1 inch
              left: 1440, // 1 inch
            },
          },
        },
        children: paragraphs,
      },
    ],
  });

  // Generate and download
  Packer.toBlob(doc)
    .then((blob) => {
      saveAs(blob, filename);
    })
    .catch((error) => {
      console.error("Error generating Word document:", error);
    });
}

// Helper functions
function isMainHeading(line) {
  return /^#{1,3}\s+/.test(line) || /^\d+\.\s+[A-Z]/.test(line);
}

function isSubHeading(line) {
  return /^#{4,6}\s+/.test(line) || /^\d+\.\d+\s+/.test(line);
}

function isBulletPoint(line) {
  return /^[-*]\s+/.test(line);
}

function isNumberedList(line) {
  return /^\d+\.\s+/.test(line) && !/^\d+\.\d+/.test(line);
}

function isBoldStatement(line) {
  return line.includes("**") || line.endsWith(":");
}

function getHeadingLevel(line) {
  const hashCount = (line.match(/^#+/) || [""])[0].length;
  if (hashCount === 1) return HeadingLevel.HEADING_1;
  if (hashCount === 2) return HeadingLevel.HEADING_2;
  if (hashCount === 3) return HeadingLevel.HEADING_3;
  if (hashCount >= 4) return HeadingLevel.HEADING_4;

  // For numbered headings
  if (/^\d+\.\s+/.test(line)) return HeadingLevel.HEADING_2;
  if (/^\d+\.\d+\s+/.test(line)) return HeadingLevel.HEADING_3;

  return HeadingLevel.HEADING_2;
}

function getHeadingFontSize(level) {
  switch (level) {
    case HeadingLevel.HEADING_1:
      return 32; // 16pt
    case HeadingLevel.HEADING_2:
      return 28; // 14pt
    case HeadingLevel.HEADING_3:
      return 26; // 13pt
    case HeadingLevel.HEADING_4:
      return 24; // 12pt
    default:
      return 24;
  }
}

function processInlineFormatting(text) {
  const runs = [];
  let currentText = text;
  let currentIndex = 0;

  // Process **bold** text
  const boldRegex = /\*\*(.*?)\*\*/g;
  let lastIndex = 0;
  let match;

  while ((match = boldRegex.exec(text)) !== null) {
    // Add text before bold
    if (match.index > lastIndex) {
      const beforeText = text.substring(lastIndex, match.index);
      if (beforeText) {
        runs.push(
          new TextRun({
            text: beforeText,
            size: 22, // 11pt
          })
        );
      }
    }

    // Add bold text
    runs.push(
      new TextRun({
        text: match[1],
        bold: true,
        size: 22, // 11pt
      })
    );

    lastIndex = match.index + match[0].length;
  }

  // Add remaining text
  if (lastIndex < text.length) {
    const remainingText = text.substring(lastIndex);
    if (remainingText) {
      runs.push(
        new TextRun({
          text: remainingText,
          size: 22, // 11pt
        })
      );
    }
  }

  // If no bold formatting was found, return the whole text
  if (runs.length === 0) {
    runs.push(
      new TextRun({
        text: text,
        size: 22, // 11pt
        bold: text.endsWith(":"), // Make text ending with : bold
      })
    );
  }

  return runs;
}

// Export functions
export { createWordDoc, createPDF, createWordDocFromMarkdown };
