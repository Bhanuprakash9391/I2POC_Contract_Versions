export function Input({ className = "", ...props }) {
    return (
        <input
            className={`px-3 py-2 rounded-md border border-gray-300 focus:outline-none focus:ring-2 focus:ring-purple-400 text-sm ${className}`}
            {...props}
        />
    );
}
