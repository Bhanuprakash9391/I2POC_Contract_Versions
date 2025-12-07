import { useState } from "react";
import { useChat } from "../../ChatContext";

export default function ContractSectionsDisplay() {
  const { contractSections, setContractSections, setInitialChatStep } = useChat();
  // const [sections, setPocSteps] = useState([
  //   {
  //     section_heading: "Introduction",
  //     section_purpose: "Provides context and objectives for the Contract.",
  //     subsections: [
  //       {
  //         subsection_heading: "Purpose",
  //         subsection_definition: "Explains the intent and objectives of the Contract.",
  //       },
  //     ],
  //   },
  //   {
  //     section_heading: "Parties and Definitions",
  //     section_purpose: "Identifies the contracting parties and defines key terms used in the contract.",
  //     subsections: [
  //       {
  //         subsection_heading: "Parties Information",
  //         subsection_definition: "Details the legal names and contact information of all parties.",
  //       },
  //     ],
  //   },
  // ]);

  const [expandedSections, setExpandedSections] = useState(new Set());
  const [editingSection, setEditingSection] = useState(null);
  const [editingSubsection, setEditingSubsection] = useState(null);

  console.log("ContractSectionDisplayComponent");

  const colors = [
    "bg-blue-50 border-blue-200 hover:bg-blue-100",
    "bg-green-50 border-green-200 hover:bg-green-100",
    "bg-purple-50 border-purple-200 hover:bg-purple-100",
    "bg-orange-50 border-orange-200 hover:bg-orange-100",
  ];

  const toggleSection = (index) => {
    const newExpanded = new Set(expandedSections);
    if (newExpanded.has(index)) {
      newExpanded.delete(index);
    } else {
      newExpanded.add(index);
    }
    setExpandedSections(newExpanded);
  };

  const deleteSection = (index) => {
    setContractSections(contractSections.filter((_, i) => i !== index));
  };

  const updateSection = (index, field, value) => {
    const updatedSections = [...contractSections];
    updatedSections[index][field] = value;
    setContractSections(updatedSections);
  };

  const deleteSubsection = (sectionIndex, subsectionIndex) => {
    const section = contractSections[sectionIndex];
    if (section.subsections.length <= 1) {
      alert("At least one subsection is required");
      return;
    }
    const updatedSections = [...contractSections];
    updatedSections[sectionIndex].subsections = updatedSections[sectionIndex].subsections.filter((_, i) => i !== subsectionIndex);
    setContractSections(updatedSections);
  };

  const updateSubsection = (sectionIndex, subsectionIndex, field, value) => {
    const updatedSections = [...contractSections];
    updatedSections[sectionIndex].subsections[subsectionIndex][field] = value;
    setContractSections(updatedSections);
  };

  return (
    <div className="min-h-screen p-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          {/* <h1 className="text-4xl font-bold text-gray-800 mb-4">POC Documentation Structure</h1> */}
          <p className="text-lg text-gray-600">Based on idea provided, we have suggest the following sections and subsections.</p>
        </div>


        {/* Sections */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* <div className="flex gap-6 flex-wrap"> */}
          {contractSections.map((section, sectionIndex) => (
            <div
              key={sectionIndex}
              className={`${colors[sectionIndex % colors.length]} border-2 rounded-xl p-6 shadow-md ${expandedSections.has(sectionIndex) ? "" : "max-h-48"} `}
            >
              {/* Section Header */}
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  {/* <div className="w-8 h-8 rounded-full bg-white border-2 border-gray-300 flex items-center justify-center text-gray-700 font-bold text-sm">{sectionIndex + 1}</div> */}
                  <button onClick={() => toggleSection(sectionIndex)} className="text-gray-600 hover:text-gray-800">
                    {expandedSections.has(sectionIndex) ? (
                      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="purple">
                        <path d="M5 8l7 11 7-11z" />
                      </svg>
                    ) : (
                      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="purple">
                        <path d="M8 5v14l11-7z" />
                      </svg>
                    )}
                  </button>
                </div>
                <div className="flex gap-2">
                  <button onClick={() => setEditingSection(sectionIndex)} className="text-purple-600 hover:text-purple-800 text-sm">
                    {/* Edit */}
                    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="purple">
                      <path d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04a1.003 1.003 0 0 0 0-1.42l-2.34-2.34a1.003 1.003 0 0 0-1.42 0l-1.83 1.83 3.75 3.75 1.84-1.82z" />
                    </svg>
                  </button>
                  <button onClick={() => deleteSection(sectionIndex)} className="text-red-600 hover:text-red-800 text-sm">
                    {/* Delete */}
                    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="#dc2626">
                      <path d="M6 19a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z" />
                    </svg>
                  </button>
                </div>
              </div>

              {/* Section Content */}
              {editingSection === sectionIndex ? (
                <div className="space-y-4 text-left">
                  <div>
                    <label className="font-semibold block text-sm font-medium text-gray-700 mb-1">Section Heading</label>
                    <input type="text" value={section.section_heading} onChange={(e) => updateSection(sectionIndex, "section_heading", e.target.value)} className="w-full p-2 border border-gray-300 rounded-md" />
                  </div>
                  <div>
                    <label className="font-semibold block text-sm font-medium text-gray-700 mb-1">Section Purpose</label>
                    <textarea
                      value={section.section_purpose}
                      onChange={(e) => updateSection(sectionIndex, "section_purpose", e.target.value)}
                      className="w-full p-2 border border-gray-300 rounded-md h-20"
                    />
                  </div>
                  <div className="flex gap-2">
                    <button onClick={() => setEditingSection(null)} className="startPocButton">
                      Save
                    </button>
                    <button onClick={() => setEditingSection(null)} className="bg-gray-50 border border-gray-200 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-400">
                      Cancel
                    </button>
                  </div>
                </div>
              ) : (
                <div>
                  <h3 className="text-xl font-semibold text-gray-800 mb-2">{section.section_heading}</h3>
                  <p className="text-gray-600 mb-4">{section.section_purpose}</p>
                </div>
              )}

                  {/* Subsections */}
                  {expandedSections.has(sectionIndex) && (
                    <div className="mt-6 pt-4 border-t-2">
                      <div className="flex justify-between items-center mb-4">
                        <h4 className="text-lg font-medium text-gray-800">Subsections</h4>
                        {/* Add Subsection button removed */}
                      </div>


                  <div className="space-y-3">
                    {section?.subsections?.map((subsection, subsectionIndex) => (
                      <div key={subsectionIndex} className="bg-white p-4 rounded-lg border border-gray-200">
                        <div className="flex justify-between items-start mb-2">
                          <div className="flex-1">
                            {editingSubsection === `${sectionIndex}-${subsectionIndex}` ? (
                              <div className="space-y-3 text-left">
                                <div>
                                  <label className="font-semibold block text-sm font-medium text-gray-700 mb-1">Subsection Heading</label>
                                  <input
                                    type="text"
                                    value={subsection.subsection_heading}
                                    onChange={(e) => updateSubsection(sectionIndex, subsectionIndex, "subsection_heading", e.target.value)}
                                    className="w-full p-2 border border-gray-300 rounded-md"
                                  />
                                </div>
                                <div>
                                  <label className="font-semibold block text-sm font-medium text-gray-700 mb-1">Subsection Definition</label>
                                  <textarea
                                    value={subsection.subsection_definition}
                                    onChange={(e) => updateSubsection(sectionIndex, subsectionIndex, "subsection_definition", e.target.value)}
                                    className="w-full p-2 border border-gray-300 rounded-md h-16"
                                  />
                                </div>
                                <div className="flex gap-2">
                                  <button onClick={() => setEditingSubsection(null)} className="bg-green-600 text-white px-3 py-1 rounded-lg text-sm hover:bg-green-700">
                                    Save
                                  </button>
                                  <button
                                    onClick={() => setEditingSubsection(null)}
                                    className="bg-gray-50 border border-gray-200 text-gray-700 px-3 py-1 rounded-lg text-sm hover:bg-gray-400"
                                  >
                                    Cancel
                                  </button>
                                </div>
                              </div>
                            ) : (
                              <div className="text-left">
                                <h5 className="font-semibold text-gray-800 mb-1">{subsection.subsection_heading}</h5>
                                <p className="text-gray-600 text-sm">{subsection.subsection_definition}</p>
                              </div>
                            )}
                          </div>
                          {editingSubsection !== `${sectionIndex}-${subsectionIndex}` && (
                            <div className="flex gap-2 ml-4">
                              <button onClick={() => setEditingSubsection(`${sectionIndex}-${subsectionIndex}`)} className="text-purple-600 hover:text-purple-800 text-sm">
                                Edit
                              </button>
                              <button onClick={() => deleteSubsection(sectionIndex, subsectionIndex)} className="text-red-600 hover:text-red-800 text-sm">
                                Delete
                              </button>
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Add Section Button - Removed */}
        <div className="mt-6 text-center">
          <div className="flex gap-6 items-center justify-center">
            {/* Add New Section button removed */}
            <button className="startPocButton" onClick={() => setInitialChatStep("done")}>
              Start Drafting Contract
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
