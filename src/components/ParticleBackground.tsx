import { useEffect, useRef, useCallback, useState } from 'react';
import * as THREE from 'three';

interface ParticleBackgroundProps {
  className?: string;
  particleCount?: number;
  sphereRadius?: number;
  particleSize?: number;
  rotationSpeed?: {
    x: number;
    y: number;
  };
  colorSpeed?: number;
  alpha?: number;
}

/**
 * Three.js particle background component with animated spherical particle cloud
 * Features color cycling, smooth rotation, and responsive sizing
 */
export const ParticleBackground: React.FC<ParticleBackgroundProps> = ({
  className = '',
  particleCount = 1500,
  sphereRadius = 1.8,
  particleSize = 0.02,
  rotationSpeed = { x: 0.0005, y: 0.001 },
  colorSpeed = 0.2,
  alpha = 0.7
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const sceneRef = useRef<THREE.Scene | null>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);
  const pointCloudRef = useRef<THREE.Points | null>(null);
  const materialRef = useRef<THREE.PointsMaterial | null>(null);
  const animationIdRef = useRef<number | null>(null);
  const hueRef = useRef<number>(0);
  const [isReducedMotion, setIsReducedMotion] = useState(false);

  // Check for reduced motion preference
  useEffect(() => {
    if (typeof window !== 'undefined' && window.matchMedia) {
      const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
      setIsReducedMotion(mediaQuery.matches);
      
      const handleChange = () => setIsReducedMotion(mediaQuery.matches);
      mediaQuery.addEventListener('change', handleChange);
      
      return () => mediaQuery.removeEventListener('change', handleChange);
    }
  }, []);

  // Check WebGL support
  const isWebGLSupported = useCallback(() => {
    try {
      const canvas = document.createElement('canvas');
      const context = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
      return !!context;
    } catch (error) {
      return false;
    }
  }, []);

  // Detect mobile device for performance optimization
  const isMobileDevice = useCallback(() => {
    return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) ||
           window.innerWidth < 768;
  }, []);

  // Handle window resize
  const handleResize = useCallback(() => {
    if (!containerRef.current || !cameraRef.current || !rendererRef.current) return;

    const { offsetWidth, offsetHeight } = containerRef.current;
    
    cameraRef.current.aspect = offsetWidth / offsetHeight;
    cameraRef.current.updateProjectionMatrix();
    rendererRef.current.setSize(offsetWidth, offsetHeight);
  }, []);

  // Initialize Three.js scene
  const initScene = useCallback(() => {
    if (!containerRef.current || !isWebGLSupported()) {
      console.warn('WebGL not supported, ParticleBackground will not render');
      return;
    }

    const container = containerRef.current;
    const { offsetWidth, offsetHeight } = container;
    const isMobile = isMobileDevice();

    // Reduce particle count on mobile for better performance
    const adjustedParticleCount = isMobile ? Math.min(particleCount, 800) : particleCount;

    // Scene setup
    const scene = new THREE.Scene();
    sceneRef.current = scene;

    // Camera setup
    const camera = new THREE.PerspectiveCamera(75, offsetWidth / offsetHeight, 0.1, 1000);
    camera.position.z = 5;
    cameraRef.current = camera;

    // Renderer setup with mobile optimizations
    const renderer = new THREE.WebGLRenderer({ 
      alpha: true,
      antialias: !isMobile, // Disable antialiasing on mobile for performance
      powerPreference: 'low-power' // Optimize for battery life
    });
    renderer.setSize(offsetWidth, offsetHeight);
    renderer.setClearColor(0x000000, 0); // Transparent background
    
    // Lower pixel ratio on mobile for better performance
    renderer.setPixelRatio(isMobile ? 1 : Math.min(window.devicePixelRatio, 2));
    rendererRef.current = renderer;

    // Clear container and append renderer
    container.innerHTML = '';
    container.appendChild(renderer.domElement);

    // Create particle geometry
    const geometry = new THREE.BufferGeometry();
    const positions: number[] = [];

    // Generate spherical particle positions
    for (let i = 0; i < adjustedParticleCount; i++) {
      const theta = 2 * Math.PI * Math.random();
      const phi = Math.acos(2 * Math.random() - 1);
      const r = sphereRadius;
      const x = r * Math.sin(phi) * Math.cos(theta);
      const y = r * Math.sin(phi) * Math.sin(theta);
      const z = r * Math.cos(phi);
      positions.push(x, y, z);
    }

    geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));

    // Create particle material with mobile optimizations
    const material = new THREE.PointsMaterial({
      size: isMobile ? particleSize * 1.5 : particleSize, // Slightly larger particles on mobile
      vertexColors: false,
      transparent: true,
      opacity: alpha,
      sizeAttenuation: true
    });
    materialRef.current = material;

    // Create point cloud
    const pointCloud = new THREE.Points(geometry, material);
    scene.add(pointCloud);
    pointCloudRef.current = pointCloud;

    // Add resize listener
    window.addEventListener('resize', handleResize);
  }, [isWebGLSupported, particleCount, sphereRadius, particleSize, alpha, handleResize, isMobileDevice]);

  // Animation loop
  const animate = useCallback(() => {
    if (!sceneRef.current || !cameraRef.current || !rendererRef.current || !pointCloudRef.current || !materialRef.current) {
      return;
    }

    // Skip animation if user prefers reduced motion
    if (!isReducedMotion) {
      // Update rotation
      pointCloudRef.current.rotation.x += rotationSpeed.x;
      pointCloudRef.current.rotation.y += rotationSpeed.y;

      // Update color cycling
      hueRef.current = (hueRef.current + colorSpeed) % 360;
      const color = new THREE.Color(`hsl(${hueRef.current}, 70%, 60%)`);
      materialRef.current.color.set(color);
    }

    // Render scene
    rendererRef.current.render(sceneRef.current, cameraRef.current);

    // Continue animation
    animationIdRef.current = requestAnimationFrame(animate);
  }, [rotationSpeed, colorSpeed, isReducedMotion]);

  // Cleanup function
  const cleanup = useCallback(() => {
    // Cancel animation
    if (animationIdRef.current) {
      cancelAnimationFrame(animationIdRef.current);
      animationIdRef.current = null;
    }

    // Remove resize listener
    window.removeEventListener('resize', handleResize);

    // Dispose Three.js objects
    if (pointCloudRef.current) {
      pointCloudRef.current.geometry.dispose();
      if (materialRef.current) {
        materialRef.current.dispose();
      }
    }

    if (rendererRef.current) {
      rendererRef.current.dispose();
    }

    // Clear container
    if (containerRef.current) {
      containerRef.current.innerHTML = '';
    }

    // Reset refs
    sceneRef.current = null;
    rendererRef.current = null;
    cameraRef.current = null;
    pointCloudRef.current = null;
    materialRef.current = null;
  }, [handleResize]);

  // Initialize scene on mount
  useEffect(() => {
    initScene();
    
    // Start animation if scene was initialized
    if (sceneRef.current) {
      animate();
    }

    // Cleanup on unmount
    return cleanup;
  }, [initScene, animate, cleanup]);

  // Don't render anything if reduced motion is preferred and no WebGL support
  if (isReducedMotion && !isWebGLSupported()) {
    return null;
  }

  return (
    <div
      ref={containerRef}
      className={`absolute inset-0 pointer-events-none overflow-hidden ${className}`}
      style={{ zIndex: -1 }}
      aria-hidden="true"
    />
  );
};

export default ParticleBackground;