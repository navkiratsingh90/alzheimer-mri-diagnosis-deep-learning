export interface PredictResponse {
	predicted_class: string;        // "Non-Demented", "Very Mild", "Mild", "Moderate"
	confidence: number;             // 0-1
	all_confidences: {
	  [key: string]: number;        // "Non-Demented": 0.01, "Very Mild": 0.03, ...
	};
	gradcam_base64: string;         // data:image/png;base64,...
  }