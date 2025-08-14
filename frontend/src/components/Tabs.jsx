import React from "react";
export default function Tabs({ tabs, value, onChange }){
  return (
    <div className="flex gap-2 border-b border-zinc-200">
      {tabs.map((t) => (
        <button key={t}
          className={`px-3 py-2 -mb-[1px] border-b-2 ${value===t?"border-zinc-900 text-zinc-900":"border-transparent text-zinc-500 hover:text-zinc-800"}`}
          onClick={() => onChange(t)}>{t}</button>
      ))}
    </div>
  );
}