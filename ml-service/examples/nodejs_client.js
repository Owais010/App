/**
 * Node.js Integration Example for Adaptive Learning Intelligence Engine
 *
 * This module provides a client for interacting with the ML microservice.
 * Uses axios for HTTP requests.
 *
 * Install dependencies:
 *   npm install axios
 */

const axios = require("axios");

// Configuration
const ML_SERVICE_URL = process.env.ML_SERVICE_URL || "http://localhost:8000";
const REQUEST_TIMEOUT = 5000; // 5 seconds

// Create axios instance with default config
const mlClient = axios.create({
  baseURL: ML_SERVICE_URL,
  timeout: REQUEST_TIMEOUT,
  headers: {
    "Content-Type": "application/json",
    Accept: "application/json",
  },
});

/**
 * Check health of the ML service
 * @returns {Promise<Object>} Health status
 */
async function checkHealth() {
  try {
    const response = await mlClient.get("/health");
    return {
      success: true,
      data: response.data,
    };
  } catch (error) {
    return {
      success: false,
      error: error.message,
    };
  }
}

/**
 * Get predictions from the ML service
 *
 * @param {Object} learnerData - Learner data for prediction
 * @param {string} learnerData.user_id - Unique user identifier
 * @param {string} learnerData.topic_id - Topic identifier
 * @param {number} learnerData.attempt_count - Total attempts (>= 1)
 * @param {number} learnerData.correct_attempts - Correct attempts (>= 0)
 * @param {number} learnerData.avg_response_time - Average response time in seconds
 * @param {number} learnerData.self_confidence_rating - Self confidence (0-1)
 * @param {number} learnerData.difficulty_feedback - Difficulty feedback (1-5)
 * @param {number} learnerData.session_duration - Session duration in minutes
 * @param {number} learnerData.previous_mastery_score - Previous mastery (0-1)
 * @param {number} learnerData.time_since_last_attempt - Hours since last attempt
 * @returns {Promise<Object>} Prediction results
 */
async function getPrediction(learnerData) {
  try {
    // Validate required fields
    const requiredFields = [
      "user_id",
      "topic_id",
      "attempt_count",
      "correct_attempts",
      "avg_response_time",
      "self_confidence_rating",
      "difficulty_feedback",
      "session_duration",
      "previous_mastery_score",
      "time_since_last_attempt",
    ];

    for (const field of requiredFields) {
      if (learnerData[field] === undefined || learnerData[field] === null) {
        throw new Error(`Missing required field: ${field}`);
      }
    }

    // Make prediction request
    const response = await mlClient.post("/predict", learnerData);

    return {
      success: true,
      data: response.data,
      requestId: response.headers["x-request-id"],
      processTimeMs: parseFloat(response.headers["x-process-time-ms"]),
    };
  } catch (error) {
    // Handle different error types
    if (error.response) {
      // Server responded with error
      return {
        success: false,
        error: error.response.data.detail || "Server error",
        statusCode: error.response.status,
      };
    } else if (error.request) {
      // No response received
      return {
        success: false,
        error: "ML service unavailable",
        statusCode: 503,
      };
    } else {
      // Request setup error
      return {
        success: false,
        error: error.message,
        statusCode: 400,
      };
    }
  }
}

/**
 * Determine next content based on adaptation action
 *
 * @param {string} adaptationAction - Action from ML service
 * @param {Object} currentContent - Current content context
 * @returns {Object} Next content recommendation
 */
function applyAdaptationLogic(adaptationAction, currentContent) {
  const recommendations = {
    add_foundation_resources: {
      action: "show_prerequisites",
      message: "Building foundational knowledge",
      contentType: "tutorial",
      difficultyAdjustment: -2,
    },
    reduce_difficulty: {
      action: "simplify_content",
      message: "Adjusting to easier content",
      contentType: "practice",
      difficultyAdjustment: -1,
    },
    increase_difficulty: {
      action: "advance_content",
      message: "Ready for more challenging content",
      contentType: "challenge",
      difficultyAdjustment: 1,
    },
    continue_current_path: {
      action: "maintain_path",
      message: "Continue current learning path",
      contentType: "standard",
      difficultyAdjustment: 0,
    },
  };

  return (
    recommendations[adaptationAction] ||
    recommendations["continue_current_path"]
  );
}

/**
 * Full integration example: Get prediction and apply business logic
 */
async function processLearnerSession(learnerData) {
  console.log("Processing learner session...");
  console.log("Input:", JSON.stringify(learnerData, null, 2));

  // Get prediction from ML service
  const result = await getPrediction(learnerData);

  if (!result.success) {
    console.error("Prediction failed:", result.error);
    return null;
  }

  console.log("\nPrediction Results:");
  console.log("Request ID:", result.requestId);
  console.log("Process Time:", result.processTimeMs, "ms");
  console.log("Skill Gap:", JSON.stringify(result.data.skill_gap));
  console.log("Difficulty:", JSON.stringify(result.data.difficulty));
  console.log("Ranking Score:", result.data.ranking.ranking_score);
  console.log("Adaptation:", result.data.adaptation.action);

  // Apply business logic based on adaptation
  const recommendation = applyAdaptationLogic(result.data.adaptation.action, {
    topicId: learnerData.topic_id,
  });

  console.log("\nBusiness Logic Recommendation:");
  console.log(JSON.stringify(recommendation, null, 2));

  return {
    prediction: result.data,
    recommendation: recommendation,
  };
}

// Example usage
async function main() {
  console.log("=".repeat(60));
  console.log("Adaptive Learning Intelligence Engine - Node.js Client");
  console.log("=".repeat(60));

  // Check service health first
  console.log("\nChecking ML service health...");
  const health = await checkHealth();

  if (!health.success) {
    console.error("ML service is not available:", health.error);
    console.log("Make sure the ML service is running at:", ML_SERVICE_URL);
    return;
  }

  console.log("ML Service Status:", health.data.status);
  console.log("Models Loaded:", health.data.models_loaded);
  console.log("Version:", health.data.version);

  // Example learner data
  const exampleLearner = {
    user_id: "user_12345",
    topic_id: "topic_algebra_101",
    attempt_count: 15,
    correct_attempts: 9,
    avg_response_time: 45.5,
    self_confidence_rating: 0.65,
    difficulty_feedback: 3,
    session_duration: 25.0,
    previous_mastery_score: 0.55,
    time_since_last_attempt: 24.0,
  };

  console.log("\n" + "=".repeat(60));
  console.log("Processing Example Learner");
  console.log("=".repeat(60));

  await processLearnerSession(exampleLearner);

  // Example with struggling learner
  const strugglingLearner = {
    user_id: "user_67890",
    topic_id: "topic_calculus_201",
    attempt_count: 20,
    correct_attempts: 5,
    avg_response_time: 120.0,
    self_confidence_rating: 0.3,
    difficulty_feedback: 5,
    session_duration: 45.0,
    previous_mastery_score: 0.25,
    time_since_last_attempt: 72.0,
  };

  console.log("\n" + "=".repeat(60));
  console.log("Processing Struggling Learner");
  console.log("=".repeat(60));

  await processLearnerSession(strugglingLearner);

  // Example with advanced learner
  const advancedLearner = {
    user_id: "user_11111",
    topic_id: "topic_physics_301",
    attempt_count: 10,
    correct_attempts: 9,
    avg_response_time: 20.0,
    self_confidence_rating: 0.9,
    difficulty_feedback: 2,
    session_duration: 15.0,
    previous_mastery_score: 0.85,
    time_since_last_attempt: 12.0,
  };

  console.log("\n" + "=".repeat(60));
  console.log("Processing Advanced Learner");
  console.log("=".repeat(60));

  await processLearnerSession(advancedLearner);
}

// Export functions for use as module
module.exports = {
  checkHealth,
  getPrediction,
  applyAdaptationLogic,
  processLearnerSession,
};

// Run if executed directly
if (require.main === module) {
  main().catch(console.error);
}
