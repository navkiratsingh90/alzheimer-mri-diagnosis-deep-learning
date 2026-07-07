import React from 'react'

export default function LoadingSpinner() {
	return (
	  <div className="flex justify-center items-center py-8">
		<div className="w-8 h-8 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin"></div>
		<span className="ml-3 text-slate-600">Analyzing MRI...</span>
	  </div>
	);
  }