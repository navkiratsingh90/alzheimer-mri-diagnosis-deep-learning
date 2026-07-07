export interface User {
	id: number;
	username: string;
	role: "user" | "admin";
  }
  
  export interface Prediction {
	id: number;
	user_id: number;
	username?: string; // only populated in admin views
	image_path: string;
	result: string;
	confidence: number;
	timestamp: string;
  }
  
  export interface AuthContextType {
	user: User | null;
	loading: boolean;
	login: (username: string, password: string) => Promise<void>;
	register: (username: string, password: string) => Promise<void>;
	logout: () => Promise<void>;
	isAdmin: boolean;
  }
  
  export interface LoginCredentials {
	username: string;
	password: string;
  }
  
  export interface RegisterCredentials {
	username: string;
	password: string;
  }
  
  export interface ChatRequest {
	question: string;
  }
  
  export interface ChatResponse {
	answer: string;
  }
  
  export interface ApiError {
	detail: string;
  }