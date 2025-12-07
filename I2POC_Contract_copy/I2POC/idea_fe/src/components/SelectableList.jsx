import { useChat } from "../ChatContext";
// import "./SelectableList.css"; // for modular CSS, or use Tailwind below

export default function SelectableList() {
  //   const [selected, setSelected] = useState(null);
  const { input, setInput, titles } = useChat();

  return (
    <div className="flex items-center justify-left p-4">
      <div className=" max-w-md space-y-4 flex flex-col items-left">
        {titles.map((option, index) => (
          <button
            key={index}
            onClick={() => setInput(option)}
            className={`cursor-pointer rounded-md px-4 py-3 text-white text-sm font-semibold
              ${input === option ? "bg-gradient-to-r from-yellow-400 to-yellow-600" : "bg-purple-500 hover:bg-purple-400 border border-purple-400"}`}
          >
            {option}
          </button>
        ))}
      </div>
    </div>
  );
}
