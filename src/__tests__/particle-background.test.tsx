import { render } from '@testing-library/react';
import { vi } from 'vitest';
import { ParticleBackground } from '@/components/ParticleBackground';

// Mock Three.js since it requires WebGL context which isn't available in tests
vi.mock('three', () => ({
  Scene: vi.fn().mockImplementation(() => ({})),
  PerspectiveCamera: vi.fn().mockImplementation(() => ({
    position: { z: 5 },
    aspect: 1,
    updateProjectionMatrix: vi.fn(),
  })),
  WebGLRenderer: vi.fn().mockImplementation(() => ({
    setSize: vi.fn(),
    setClearColor: vi.fn(),
    domElement: document.createElement('canvas'),
    dispose: vi.fn(),
    render: vi.fn(),
  })),
  BufferGeometry: vi.fn().mockImplementation(() => ({
    setAttribute: vi.fn(),
    dispose: vi.fn(),
  })),
  Float32BufferAttribute: vi.fn(),
  PointsMaterial: vi.fn().mockImplementation(() => ({
    color: { set: vi.fn() },
    dispose: vi.fn(),
  })),
  Points: vi.fn().mockImplementation(() => ({
    rotation: { x: 0, y: 0 },
    geometry: { dispose: vi.fn() },
  })),
  Color: vi.fn().mockImplementation(() => ({})),
}));

// Mock requestAnimationFrame
global.requestAnimationFrame = vi.fn((callback: FrameRequestCallback) => {
  setTimeout(callback, 16);
  return 1;
});

global.cancelAnimationFrame = vi.fn();

describe('ParticleBackground', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders without crashing', () => {
    const { container } = render(<ParticleBackground />);
    
    expect(container.firstChild).toBeInTheDocument();
    expect(container.firstChild).toHaveClass('absolute', 'inset-0', 'pointer-events-none');
  });

  it('accepts custom className', () => {
    const { container } = render(<ParticleBackground className="custom-class" />);
    
    expect(container.firstChild).toHaveClass('custom-class');
  });

  it('has proper accessibility attributes', () => {
    const { container } = render(<ParticleBackground />);
    
    expect(container.firstChild).toHaveAttribute('aria-hidden', 'true');
  });

  it('has correct z-index styling', () => {
    const { container } = render(<ParticleBackground />);
    
    expect(container.firstChild).toHaveStyle({ zIndex: -1 });
  });
});