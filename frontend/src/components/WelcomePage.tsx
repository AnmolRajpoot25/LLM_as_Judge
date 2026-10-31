import React from "react";
import { ArrowRight, Check, Scale, Sparkles } from "lucide-react";
import heroImage from "../assets/llm-judge-welcome.png";
import "./WelcomePage.css";

interface WelcomePageProps {
  onNext: () => void;
  onSignIn: () => void;
}

export const WelcomePage: React.FC<WelcomePageProps> = ({ onNext, onSignIn }) => (
  <main className="welcome-shell">
    <header className="welcome-header">
      <a className="welcome-brand" href="#welcome" aria-label="LLM-Judge home">
        <span className="welcome-brand-icon"><Scale size={21} aria-hidden="true" /></span>
        <span>LLM-Judge</span>
        <span className="welcome-brand-badge">Qwen powered</span>
      </a>
      <span className="welcome-header-note"><Sparkles size={15} aria-hidden="true" /> Compare with confidence</span>
    </header>

    <section className="welcome-layout" id="welcome">
      <div className="welcome-copy">
        <div className="welcome-eyebrow"><span /> A clearer way to evaluate AI</div>
        <h1>Make every model answer <span>earn your trust.</span></h1>
        <p className="welcome-description">
          Put answers side by side, let a fine-tuned Qwen judge compare them, and see which model comes out ahead—with evidence you can inspect.
        </p>

        <div className="welcome-workflow" aria-label="How LLM-Judge works">
          <div className="welcome-workflow-step">
            <span className="welcome-step-number">01</span>
            <span className="welcome-step-text"><strong>Compare</strong><small>Run models or add answers</small></span>
          </div>
          <span className="welcome-step-line" aria-hidden="true" />
          <div className="welcome-workflow-step">
            <span className="welcome-step-number">02</span>
            <span className="welcome-step-text"><strong>Evaluate</strong><small>Score with the Qwen judge</small></span>
          </div>
          <span className="welcome-step-line" aria-hidden="true" />
          <div className="welcome-workflow-step">
            <span className="welcome-step-number">03</span>
            <span className="welcome-step-text"><strong>Choose</strong><small>Review clear rankings</small></span>
          </div>
        </div>

        <div className="welcome-actions">
          <button className="welcome-next-button" onClick={onNext}>
            <span>Next</span><ArrowRight size={18} aria-hidden="true" />
          </button>
          <p>Already have an account? <button className="welcome-signin-link" onClick={onSignIn}>Sign in</button></p>
        </div>

        <div className="welcome-points">
          <span><Check size={15} aria-hidden="true" /> Pairwise model evaluation</span>
          <span><Check size={15} aria-hidden="true" /> Inspectable results</span>
          <span><Check size={15} aria-hidden="true" /> Your provider keys</span>
        </div>
      </div>

      <figure className="welcome-visual">
        <img src={heroImage} alt="Researchers comparing AI model evaluation results on a screen" />
        <div className="welcome-visual-wash" aria-hidden="true" />
        <figcaption className="welcome-image-caption">
          <span className="welcome-caption-icon"><Sparkles size={17} aria-hidden="true" /></span>
          <span><strong>From answers to evidence</strong><small>See quality, compare outcomes, decide clearly.</small></span>
        </figcaption>
        <div className="welcome-score-card" aria-hidden="true">
          <span className="welcome-score-label">PAIRWISE RESULT</span>
          <span className="welcome-score-title">Answer A leads</span>
          <span className="welcome-score-bars"><i /><i /></span>
          <span className="welcome-score-foot"><span>Correctness</span><b>Evaluated</b></span>
        </div>
      </figure>
    </section>

    <footer className="welcome-footer">
      <span>Built for careful model evaluation</span>
      <span><span className="welcome-footer-dot" /> Qwen-powered pairwise judging</span>
    </footer>
  </main>
);
