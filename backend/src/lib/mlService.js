/**
 * ML Service Client — Adaptive Quiz Intelligence
 *
 * Typed client for the Python ML service (FastAPI).
 * All methods return null on failure (never crashes the quiz flow).
 *
 * @version 2.0.0
 */

const ML_API_URL = process.env.ML_API_URL || "http://localhost:8000";
const ML_API_KEY = process.env.ML_API_KEY || "default_test_key";
const ML_TIMEOUT_MS = 5000;

// ─────────────────────────────────────────────────────────────────────────────
// INTERNAL FETCH HELPER
// ─────────────────────────────────────────────────────────────────────────────

async function _mlFetch(path, body, method = "POST") {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), ML_TIMEOUT_MS);

  try {
    const opts = {
      method,
      headers: {
        "Content-Type": "application/json",
        "X-API-Key": ML_API_KEY,
      },
      signal: controller.signal,
    };
    if (body && method !== "GET") {
      opts.body = JSON.stringify(body);
    }

    const response = await fetch(`${ML_API_URL}${path}`, opts);

    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      console.warn(`ML Service ${path} error:`, err.detail || response.status);
      return null;
    }

    return await response.json();
  } catch (error) {
    if (error.name === "AbortError") {
      console.warn(`ML Service ${path} timed out after ${ML_TIMEOUT_MS}ms`);
    } else {
      console.warn(`ML Service ${path} unavailable:`, error.message);
    }
    return null;
  } finally {
    clearTimeout(timeout);
  }
}

// ╔═══════════════════════════════════════════════════════════════════════════╗
// ║  GENERIC PREDICT (backward compat)                                     ║
// ╚═══════════════════════════════════════════════════════════════════════════╝

/**
 * Generic prediction — backward compatible with original client.
 * @param {Object} payload - { user_id, topic_id, prediction_type, features? }
 * @returns {Promise<Object|null>}
 */
export async function getMLPrediction(payload) {
  return _mlFetch("/predict", payload);
}

// ╔═══════════════════════════════════════════════════════════════════════════╗
// ║  TYPED ENDPOINTS                                                       ║
// ╚═══════════════════════════════════════════════════════════════════════════╝

/**
 * Predict user level for a topic.
 * @param {string} userId
 * @param {string} topicId
 * @param {Object} [features] - Pre-computed feature vector (optional)
 * @returns {Promise<{predicted_level: string, confidence: number, probabilities: Object, model_used: string}|null>}
 */
export async function predictLevel(userId, topicId, features = null) {
  const body = { user_id: userId, topic_id: topicId };
  if (features) body.features = features;
  return _mlFetch("/predict/level", body);
}

/**
 * Get recommended difficulty for next question.
 * @param {string} userId
 * @param {string} topicId
 * @param {Object} [features]
 * @returns {Promise<{recommended_difficulty: string, predicted_success_prob: number, confidence: number}|null>}
 */
export async function predictDifficulty(userId, topicId, features = null) {
  const body = { user_id: userId, topic_id: topicId };
  if (features) body.features = features;
  return _mlFetch("/predict/difficulty", body);
}

/**
 * Predict P(correct) per difficulty for next question selection.
 * @param {string} userId
 * @param {string} topicId
 * @param {string[]} [candidateDifficulties]
 * @param {Object} [features]
 * @returns {Promise<{success_probabilities: Object, optimal_difficulty: string}|null>}
 */
export async function predictNextQuestion(
  userId,
  topicId,
  candidateDifficulties = ["easy", "medium", "hard"],
  features = null,
) {
  const body = {
    user_id: userId,
    topic_id: topicId,
    candidate_difficulties: candidateDifficulties,
  };
  if (features) body.features = features;
  return _mlFetch("/predict/next-question", body);
}

/**
 * Batch predictions for multiple topics.
 * @param {string} userId
 * @param {string[]} topicIds
 * @returns {Promise<{predictions: Array}|null>}
 */
export async function predictBatch(userId, topicIds) {
  return _mlFetch("/predict/batch", {
    user_id: userId,
    topic_ids: topicIds,
  });
}

/**
 * Get computed features for a user-topic pair.
 * @param {string} userId
 * @param {string} topicId
 * @returns {Promise<Object|null>}
 */
export async function getFeatures(userId, topicId) {
  return _mlFetch(`/features/${userId}/${topicId}`, null, "GET");
}

/**
 * Invalidate feature cache after new answers.
 * @param {string} userId
 * @param {string} [topicId]
 */
export async function invalidateCache(userId, topicId = null) {
  const params = new URLSearchParams({ user_id: userId });
  if (topicId) params.append("topic_id", topicId);
  return _mlFetch(`/cache/invalidate?${params}`, null, "POST");
}

/**
 * Check ML service health.
 * @returns {Promise<{status: string, models_loaded: Object}|null>}
 */
export async function checkHealth() {
  return _mlFetch("/health", null, "GET");
}

// ─────────────────────────────────────────────────────────────────────────────
// DEFAULT EXPORT
// ─────────────────────────────────────────────────────────────────────────────

export default {
  getMLPrediction,
  predictLevel,
  predictDifficulty,
  predictNextQuestion,
  predictBatch,
  getFeatures,
  invalidateCache,
  checkHealth,
};
