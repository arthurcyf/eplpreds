import React from "react";
export default function Card({ children, className="" }){
  return <div className={`rounded-2xl border border-zinc-200 p-4 bg-white shadow-sm ${className}`}>{children}</div>;
}