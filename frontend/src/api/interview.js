const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "";

/**
 * Fetch list of all candidates from the backend.
 * @returns {Promise<Object>} The candidates json payload
 */
export async function getCandidates() {
  const response = await fetch(`${API_BASE_URL}/api/candidates`);
  if (!response.ok) {
    throw new Error(`Failed to load candidates: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Submit start or next turn request to /api/interview.
 * @param {Object} payload The start or turn payload
 * @returns {Promise<Object>} The response JSON
 */
export async function submitInterviewTurn(payload) {
  const response = await fetch(`${API_BASE_URL}/api/interview`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: "Internal Server Error" }));
    throw new Error(errorData.detail || `Request failed with status ${response.status}`);
  }

  return response.json();
}
