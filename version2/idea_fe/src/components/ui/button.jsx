export function Button({ className = "", ...props }) {
    return (
        <button
            className={`px-4 py-2 rounded-md bg-purple-500 text-white hover:bg-purple-600 transition ${className}`}
            {...props}
        />
    );
}
