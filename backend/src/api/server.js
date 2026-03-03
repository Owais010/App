/**
 * Quiz Engine Backend — Express Server
 *
 * Mounts the assessment API routes and serves the quiz engine.
 *
 * Usage:
 *   node src/api/server.js
 *
 * Environment:
 *   PORT               — Server port (default: 3000)
 *   SUPABASE_URL       — Supabase project URL
 *   SUPABASE_SERVICE_KEY — Supabase service_role JWT
 */

import "dotenv/config";
import express from "express";
import cors from "cors";
import assessmentRoutes from "./assessmentRoutes.js";
import adminRoutes from "./adminRoutes.js";

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json());

// Routes
app.use("/api/admin", adminRoutes);
app.use("/api", assessmentRoutes);

// Root
app.get("/", (req, res) => {
  res.json({
    service: "quiz-engine-backend",
    version: "1.0.0",
    docs: "/api/health",
  });
});

// Start
app.listen(PORT, () => {
  console.log(`Quiz Engine Backend running on http://localhost:${PORT}`);
  console.log(`Health check: http://localhost:${PORT}/api/health`);
});

export default app;
