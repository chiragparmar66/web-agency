import { Variants, Transition } from "motion/react";

/**
 * Premium, subtle motion configuration for Nexus Studio.
 * Designed to feel human-crafted, responsive, and calm.
 * Avoids bouncy, distracting, or sluggish animations.
 */

// Refined easing curve (gentle deceleration)
export const MOTION_TRANSITION: Transition = {
  duration: 0.45,
  ease: [0.16, 1, 0.3, 1], // Custom smooth ease-out
};

export const MOTION_FAST: Transition = {
  duration: 0.25,
  ease: [0.16, 1, 0.3, 1],
};

// Subtle fade-up entrance
export const fadeUpVariants: Variants = {
  hidden: {
    opacity: 0,
    y: 14,
  },
  visible: {
    opacity: 1,
    y: 0,
    transition: MOTION_TRANSITION,
  },
};

// Simple fade-in
export const fadeInVariants: Variants = {
  hidden: {
    opacity: 0,
  },
  visible: {
    opacity: 1,
    transition: {
      duration: 0.35,
      ease: "easeOut",
    },
  },
};

// Container with staggered children reveals
export const staggerContainerVariants: Variants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.08,
      delayChildren: 0.05,
    },
  },
};

// Restrained card hover variant
export const cardHoverProps = {
  whileHover: {
    y: -3,
    transition: { duration: 0.2, ease: "easeOut" },
  },
  whileTap: {
    scale: 0.99,
  },
};

// Interactive button micro-transition
export const buttonPressProps = {
  whileHover: { scale: 1.01 },
  whileTap: { scale: 0.98 },
  transition: { duration: 0.15 },
};

// Alert / notification entrance & exit
export const alertVariants: Variants = {
  hidden: {
    opacity: 0,
    y: -8,
    scale: 0.98,
  },
  visible: {
    opacity: 1,
    y: 0,
    scale: 1,
    transition: MOTION_FAST,
  },
  exit: {
    opacity: 0,
    y: -6,
    scale: 0.98,
    transition: { duration: 0.2 },
  },
};

// Mobile drawer slide-in
export const drawerVariants: Variants = {
  closed: {
    x: "-100%",
    transition: {
      duration: 0.3,
      ease: [0.16, 1, 0.3, 1],
    },
  },
  open: {
    x: 0,
    transition: {
      duration: 0.35,
      ease: [0.16, 1, 0.3, 1],
    },
  },
};

export const backdropVariants: Variants = {
  closed: { opacity: 0, transition: { duration: 0.25 } },
  open: { opacity: 1, transition: { duration: 0.25 } },
};

// Standard viewport config for scroll-triggered reveals
export const VIEWPORT_ONCE = {
  once: true,
  margin: "-40px",
};
