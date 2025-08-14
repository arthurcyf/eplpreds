import React from "react";
export default function NumberInput({ value, onChange, placeholder }){
  return (
    <input type="number" min="0" max="20" className="w-16 text-center border border-zinc-300 rounded-lg px-2 py-1"
      value={value ?? ""} placeholder={placeholder} onChange={e=>onChange(e.target.value)} />
  );
}