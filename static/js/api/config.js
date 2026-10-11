export const API_VERSION = "v1";

export const API_BASE = `/api/${API_VERSION}`;

export const API_ENDPOINTS = {
    PRICE_HISTORY: `${API_BASE}/price_history/`,
    SCRAPING: `${API_BASE}/scraping/`,
    SEARCH_BICYCLE: `${API_BASE}/search_bicycle/`,
    SIGN_IN: `${API_BASE}/signin/`,
    SIGN_UP: `${API_BASE}/signup/`,
    SIGN_OUT: `${API_BASE}/signout/`,
    SUBSCRIPTION: `${API_BASE}/subscription/`,
    UNSUBSCRIPTION: `${API_BASE}/unsubscription/`,
    GOOGLE_SIGN_IN: `${API_BASE}/auth/google/`,
    ME: `${API_BASE}/me/`,
};