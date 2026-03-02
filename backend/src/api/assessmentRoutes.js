/**
 * Assessment API Routes
 *
 * Express.js routes for quiz engine endpoints.
 * Can also be adapted for Vercel Serverless, Supabase Edge Functions, etc.
 *
 * @version 1.0.0
 * @author Person 2 - Quiz Engine Team
 */

import express from "express";
import {
  generateQuiz,
  finishAssessment,
  resumeAssessment,
  abandonAssessment,
  getRecommendations,
  getWeakTopicRecommendations,
  getSubjectRecommendations,
  updateRecommendationStatus,
  getUserProfile,
  classifyUserTopics,
  RESPONSE_CODES,
  ERROR_MESSAGES,
} from "../services/quizEngine/index.js";
import { getDashboardSummary } from "../services/dashboardService.js";

const router = express.Router();

// ============================================================================
// MIDDLEWARE
// ============================================================================

/**
 * Validate user authentication
 * In production, this should verify JWT token from Supabase Auth
 */
const requireAuth = (req, res, next) => {
  const userId =
    req.body?.userId || req.query?.userId || req.headers["x-user-id"];

  if (!userId) {
    return res.status(RESPONSE_CODES.UNAUTHORIZED).json({
      success: false,
      error: "User ID required",
    });
  }

  // Validate UUID format
  const uuidRegex =
    /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
  if (!uuidRegex.test(userId)) {
    return res.status(RESPONSE_CODES.BAD_REQUEST).json({
      success: false,
      error: ERROR_MESSAGES.INVALID_USER_ID,
    });
  }

  req.userId = userId;
  next();
};

/**
 * Request logging middleware
 */
const logRequest = (req, res, next) => {
  const start = Date.now();
  res.on("finish", () => {
    const duration = Date.now() - start;
    console.log(
      `[${new Date().toISOString()}] ${req.method} ${req.path} - ${res.statusCode} (${duration}ms)`,
    );
  });
  next();
};

router.use(logRequest);

// ============================================================================
// ASSESSMENT ENDPOINTS
// ============================================================================

/**
 * POST /start-assessment
 *
 * Generate a new quiz/assessment
 *
 * Body:
 * - userId: UUID (required)
 * - type: 'diagnostic' | 'practice' | 'retest' (default: 'diagnostic')
 * - numQuestions: number (optional)
 * - subjectId: UUID (optional, for subject-focused)
 * - topicId: UUID (optional, for topic-focused practice)
 */
router.post("/start-assessment", requireAuth, async (req, res) => {
  try {
    const {
      type = "diagnostic",
      numQuestions,
      subjectId,
      topicId,
      subjectFilter,
    } = req.body;

    // Validate assessment type
    const validTypes = ["diagnostic", "practice", "retest", "custom"];
    if (!validTypes.includes(type)) {
      return res.status(RESPONSE_CODES.BAD_REQUEST).json({
        success: false,
        error: "Invalid assessment type",
      });
    }

    // Generate quiz
    const result = await generateQuiz({
      userId: req.userId,
      type,
      numQuestions,
      subjectId,
      topicId,
      subjectFilter,
    });

    if (!result.success) {
      return res.status(RESPONSE_CODES.INTERNAL_ERROR).json(result);
    }

    return res.status(RESPONSE_CODES.CREATED).json(result);
  } catch (error) {
    console.error("Start assessment error:", error);
    return res.status(RESPONSE_CODES.INTERNAL_ERROR).json({
      success: false,
      error: error.message || ERROR_MESSAGES.DATABASE_ERROR,
    });
  }
});

/**
 * POST /finish-assessment
 *
 * Complete an assessment and get results + recommendations
 *
 * Body:
 * - userId: UUID (required)
 * - assessmentId: UUID (required)
 * - answers: Array of { questionId, selectedOption, timeTakenSeconds?, confidenceRating? }
 * - timeSpentSeconds: number (optional)
 */
router.post("/finish-assessment", requireAuth, async (req, res) => {
  try {
    const { assessmentId, answers, timeSpentSeconds } = req.body;

    // Validate required fields
    if (!assessmentId) {
      return res.status(RESPONSE_CODES.BAD_REQUEST).json({
        success: false,
        error: "Assessment ID required",
      });
    }

    if (!answers || !Array.isArray(answers)) {
      return res.status(RESPONSE_CODES.BAD_REQUEST).json({
        success: false,
        error: "Answers array required",
      });
    }

    // Finish assessment
    const result = await finishAssessment({
      userId: req.userId,
      assessmentId,
      answers,
      timeSpentSeconds,
    });

    if (!result.success) {
      const statusCode = result.error?.includes("not found")
        ? RESPONSE_CODES.NOT_FOUND
        : result.error?.includes("already completed")
          ? RESPONSE_CODES.CONFLICT
          : RESPONSE_CODES.INTERNAL_ERROR;

      return res.status(statusCode).json(result);
    }

    return res.status(RESPONSE_CODES.SUCCESS).json(result);
  } catch (error) {
    console.error("Finish assessment error:", error);
    return res.status(RESPONSE_CODES.INTERNAL_ERROR).json({
      success: false,
      error: error.message || ERROR_MESSAGES.DATABASE_ERROR,
    });
  }
});

/**
 * POST /resume-assessment
 *
 * Resume an in-progress assessment
 *
 * Body:
 * - userId: UUID (required)
 * - assessmentId: UUID (required)
 */
router.post("/resume-assessment", requireAuth, async (req, res) => {
  try {
    const { assessmentId } = req.body;

    if (!assessmentId) {
      return res.status(RESPONSE_CODES.BAD_REQUEST).json({
        success: false,
        error: "Assessment ID required",
      });
    }

    const result = await resumeAssessment(assessmentId, req.userId);

    if (!result.success) {
      return res.status(RESPONSE_CODES.NOT_FOUND).json(result);
    }

    return res.status(RESPONSE_CODES.SUCCESS).json(result);
  } catch (error) {
    console.error("Resume assessment error:", error);
    return res.status(RESPONSE_CODES.INTERNAL_ERROR).json({
      success: false,
      error: error.message,
    });
  }
});

/**
 * POST /abandon-assessment
 *
 * Abandon an in-progress assessment
 */
router.post("/abandon-assessment", requireAuth, async (req, res) => {
  try {
    const { assessmentId } = req.body;

    if (!assessmentId) {
      return res.status(RESPONSE_CODES.BAD_REQUEST).json({
        success: false,
        error: "Assessment ID required",
      });
    }

    const result = await abandonAssessment(assessmentId, req.userId);

    if (!result.success) {
      return res.status(RESPONSE_CODES.NOT_FOUND).json(result);
    }

    return res.status(RESPONSE_CODES.SUCCESS).json(result);
  } catch (error) {
    console.error("Abandon assessment error:", error);
    return res.status(RESPONSE_CODES.INTERNAL_ERROR).json({
      success: false,
      error: error.message,
    });
  }
});

// ============================================================================
// RECOMMENDATION ENDPOINTS
// ============================================================================

/**
 * GET /recommendations
 *
 * Get recommendations for user's weak topics
 *
 * Query:
 * - userId: UUID (required)
 * - limit: number (default: 5)
 */
router.get("/recommendations", requireAuth, async (req, res) => {
  try {
    const limit = parseInt(req.query.limit) || 5;

    const recommendations = await getWeakTopicRecommendations(
      req.userId,
      limit,
    );

    return res.status(RESPONSE_CODES.SUCCESS).json({
      success: true,
      recommendations,
    });
  } catch (error) {
    console.error("Get recommendations error:", error);
    return res.status(RESPONSE_CODES.INTERNAL_ERROR).json({
      success: false,
      error: error.message,
    });
  }
});

/**
 * GET /recommendations/subject/:subjectId
 *
 * Get recommendations for a specific subject
 */
router.get(
  "/recommendations/subject/:subjectId",
  requireAuth,
  async (req, res) => {
    try {
      const { subjectId } = req.params;
      const limit = parseInt(req.query.limit) || 3;

      const recommendations = await getSubjectRecommendations(
        req.userId,
        subjectId,
        limit,
      );

      return res.status(RESPONSE_CODES.SUCCESS).json({
        success: true,
        recommendations,
      });
    } catch (error) {
      console.error("Get subject recommendations error:", error);
      return res.status(RESPONSE_CODES.INTERNAL_ERROR).json({
        success: false,
        error: error.message,
      });
    }
  },
);

/**
 * POST /recommendations/:id/status
 *
 * Update recommendation status (viewed/started/completed)
 */
router.post("/recommendations/:id/status", requireAuth, async (req, res) => {
  try {
    const { id } = req.params;
    const { status } = req.body;

    if (!["viewed", "started", "completed"].includes(status)) {
      return res.status(RESPONSE_CODES.BAD_REQUEST).json({
        success: false,
        error: "Invalid status. Must be: viewed, started, or completed",
      });
    }

    const result = await updateRecommendationStatus(id, req.userId, status);

    return res
      .status(
        result.success ? RESPONSE_CODES.SUCCESS : RESPONSE_CODES.INTERNAL_ERROR,
      )
      .json(result);
  } catch (error) {
    console.error("Update recommendation status error:", error);
    return res.status(RESPONSE_CODES.INTERNAL_ERROR).json({
      success: false,
      error: error.message,
    });
  }
});

// ============================================================================
// USER STATS ENDPOINTS
// ============================================================================

/**
 * GET /user/profile
 *
 * Get user's overall performance profile
 */
router.get("/user/profile", requireAuth, async (req, res) => {
  try {
    const profile = await getUserProfile(req.userId);

    if (!profile) {
      return res.status(RESPONSE_CODES.NOT_FOUND).json({
        success: false,
        error: "No profile data found",
      });
    }

    return res.status(RESPONSE_CODES.SUCCESS).json({
      success: true,
      profile,
    });
  } catch (error) {
    console.error("Get user profile error:", error);
    return res.status(RESPONSE_CODES.INTERNAL_ERROR).json({
      success: false,
      error: error.message,
    });
  }
});

/**
 * GET /profile
 *
 * Alias for /user/profile to match exact architecture spec
 */
router.get("/profile", requireAuth, async (req, res) => {
  try {
    const profile = await getUserProfile(req.userId);

    if (!profile) {
      return res.status(RESPONSE_CODES.NOT_FOUND).json({
        success: false,
        error: "No profile data found",
      });
    }

    return res.status(RESPONSE_CODES.SUCCESS).json({
      success: true,
      profile,
    });
  } catch (error) {
    console.error("Get user profile error:", error);
    return res.status(RESPONSE_CODES.INTERNAL_ERROR).json({
      success: false,
      error: error.message,
    });
  }
});

/**
 * GET /dashboard-summary
 *
 * Aggregated endpoint for the dashboard
 */
router.get("/dashboard-summary", requireAuth, async (req, res) => {
  try {
    const result = await getDashboardSummary(req.userId);

    if (!result.success) {
      return res.status(RESPONSE_CODES.INTERNAL_ERROR).json(result);
    }

    return res.status(RESPONSE_CODES.SUCCESS).json(result);
  } catch (error) {
    console.error("Dashboard summary error:", error);
    return res.status(RESPONSE_CODES.INTERNAL_ERROR).json({
      success: false,
      error: error.message,
    });
  }
});

/**
 * POST /user/topic-levels
 *
 * Get level classifications for specific topics
 *
 * Body:
 * - userId: UUID (required)
 * - topicIds: UUID[] (required)
 */
router.post("/user/topic-levels", requireAuth, async (req, res) => {
  try {
    const { topicIds } = req.body;

    if (!topicIds || !Array.isArray(topicIds) || topicIds.length === 0) {
      return res.status(RESPONSE_CODES.BAD_REQUEST).json({
        success: false,
        error: "Topic IDs array required",
      });
    }

    const levels = await classifyUserTopics(req.userId, topicIds);

    return res.status(RESPONSE_CODES.SUCCESS).json({
      success: true,
      levels,
    });
  } catch (error) {
    console.error("Get topic levels error:", error);
    return res.status(RESPONSE_CODES.INTERNAL_ERROR).json({
      success: false,
      error: error.message,
    });
  }
});

// ============================================================================
// HEALTH CHECK
// ============================================================================

router.get("/health", (req, res) => {
  res.status(200).json({
    status: "healthy",
    service: "quiz-engine",
    timestamp: new Date().toISOString(),
  });
});

// ============================================================================
// EXPORT
// ============================================================================

export default router;
