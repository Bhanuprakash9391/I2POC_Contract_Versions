import { useChat } from "../../ChatContext";

export default function ProgressIndicator({ steps, title }) {
  const { activeSection, isDraftingComplete } = useChat();

  // Function to determine step status
  const getStepStatus = (step, index) => {
    const stepName = step.section_heading || step.title;

    // If this step matches the active section, it's the current step
    if (stepName === activeSection) {
      return "current";
    }

    // If we have an active section and this step's index is less than the active step's index,
    // it's completed
    if (activeSection) {
      const activeIndex = steps.findIndex((s) => (s.section_heading || s.title) === activeSection);
      if ((activeIndex !== -1 && index < activeIndex) || isDraftingComplete) {
        return "completed";
      }
    }

    // Otherwise, it's upcoming
    return "upcoming";
  };

  return (
    <div className="bg-transparent shadow-sm">
      <div className="max-w-4xl mx-auto px-4 py-4">
        {/* Project Title */}
        {/* <h1 className="text-4xl font-bold text-purple-800 mb-4">{title}</h1> */}

        {/* Progress Steps */}
        <div className="flex items-center justify-center">
          {steps && steps.length > 0 ? (
            steps.map((step, index) => {
              const status = getStepStatus(step, index);
              return (
                <div key={index} className="flex items-center">
                  {/* Step Circle with dynamic styling based on status */}
                  <div className="flex flex-col items-center">
                    <div
                      className={`
                        flex items-center justify-center w-6 h-6 rounded-full 
                        ${
                          status === "completed" || isDraftingComplete
                            ? " text-green-500 ring-2 ring-green-700"
                            : status === "current"
                            ? " text-purple-700 ring-2 ring-purple-700"
                            : "bg-gray-100 text-gray-600"
                        }
                        font-semibold text-sm transition-colors duration-200
                      `}
                    >
                      {status === "completed" || isDraftingComplete ? (
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                          <path
                            fillRule="evenodd"
                            d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                            clipRule="evenodd"
                          />
                        </svg>
                      ) : (
                        index + 1
                      )}
                    </div>

                    {/* Step Label with dynamic styling */}
                    <span
                      className={`
                        mt-2 text-xs font-medium text-capitalize
                        ${status === "completed" || isDraftingComplete ? "text-green-600" : status === "current" ? "text-purple-800" : "text-gray-500"}
                      `}
                    >
                      {step.section_heading || step.title}
                    </span>
                  </div>

                  {/* Connector Line with dynamic styling */}
                  {index < steps.length - 1 && (
                    <div
                      className={`
                        h-0.5 w-40 mx-2
                        ${status === "completed" || isDraftingComplete ? "bg-green-500" : status === "current" ? "bg-purple-500" : "bg-gray-200"}
                      `}
                    ></div>
                  )}
                </div>
              );
            })
          ) : (
            <div className="text-gray-500">No steps available</div>
          )}
        </div>
      </div>
    </div>
  );
}
