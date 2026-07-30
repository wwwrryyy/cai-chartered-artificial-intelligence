import { useEffect, useRef } from 'react';
import * as THREE from 'three';
import { AsciiEffect } from 'three/addons/effects/AsciiEffect.js';

export default function ASCIIText() {
  const mountRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!mountRef.current) return;

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0, 0, 0);

    const camera = new THREE.PerspectiveCamera(50, window.innerWidth / window.innerHeight, 1, 1000);
    camera.position.y = 150;
    camera.position.z = 500;

    const renderer = new THREE.WebGLRenderer({ alpha: true });
    renderer.setSize(window.innerWidth, window.innerHeight);

    const effect = new AsciiEffect(renderer, ' .:-+*=%@#', { invert: true, resolution: 0.15 });
    effect.setSize(window.innerWidth, window.innerHeight);
    effect.domElement.style.color = 'inherit';
    effect.domElement.style.backgroundColor = 'transparent';

    mountRef.current.appendChild(effect.domElement);

    // Lighting
    const pointLight1 = new THREE.PointLight(0xffffff, 3, 0, 0);
    pointLight1.position.set(500, 500, 500);
    scene.add(pointLight1);

    const pointLight2 = new THREE.PointLight(0xffffff, 1, 0, 0);
    pointLight2.position.set(-500, -500, -500);
    scene.add(pointLight2);

    const ambientLight = new THREE.AmbientLight(0xffffff, 0.2);
    scene.add(ambientLight);

    // Wave Geometry
    const geometry = new THREE.PlaneGeometry(1000, 1000, 80, 40);
    geometry.rotateX(-Math.PI / 2);

    const material = new THREE.MeshPhongMaterial({
      color: 0xffffff,
      flatShading: true,
      side: THREE.DoubleSide,
    });

    const plane = new THREE.Mesh(geometry, material);
    scene.add(plane);

    // "CAI" text as canvas texture overlay
    const canvas = document.createElement('canvas');
    canvas.width = 512;
    canvas.height = 256;
    const ctx = canvas.getContext('2d');
    if (ctx) {
      ctx.fillStyle = 'black';
      ctx.fillRect(0, 0, 512, 256);
      ctx.font = 'Bold 140px monospace';
      ctx.fillStyle = 'white';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText('CAI', 256, 128);
    }
    const textTexture = new THREE.CanvasTexture(canvas);
    const textMaterial = new THREE.MeshBasicMaterial({
      map: textTexture,
      transparent: true,
      opacity: 0.9,
      alphaTest: 0.1,
    });
    const textPlane = new THREE.Mesh(new THREE.PlaneGeometry(260, 130), textMaterial);
    textPlane.position.x = -250;
    textPlane.position.y = 300;
    textPlane.position.z = 100;
    scene.add(textPlane);

    // Animation loop
    let animationFrameId: number;
    const clock = new THREE.Clock();

    const animate = () => {
      animationFrameId = requestAnimationFrame(animate);
      const elapsedTime = clock.getElapsedTime();

      const positionAttribute = geometry.getAttribute('position');
      for (let i = 0; i < positionAttribute.count; i++) {
        const x = positionAttribute.getX(i);
        const z = positionAttribute.getZ(i);
        const y =
          Math.sin(x * 0.01 + elapsedTime * 2) * 20 +
          Math.sin(z * 0.01 + elapsedTime * 2) * 20;
        positionAttribute.setY(i, y);
      }
      positionAttribute.needsUpdate = true;
      geometry.computeVertexNormals();

      textPlane.position.x = -250;
      textPlane.position.y = 300;
      textPlane.rotation.y = 0;

      effect.render(scene, camera);
    };

    animate();

    const handleResize = () => {
      camera.aspect = window.innerWidth / window.innerHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(window.innerWidth, window.innerHeight);
      effect.setSize(window.innerWidth, window.innerHeight);
    };
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      cancelAnimationFrame(animationFrameId);
      if (mountRef.current && effect.domElement) {
        mountRef.current.removeChild(effect.domElement);
      }
      renderer.dispose();
      geometry.dispose();
      material.dispose();
      textTexture.dispose();
      textMaterial.dispose();
    };
  }, []);

  return (
    <div
      ref={mountRef}
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 0,
        pointerEvents: 'none',
        overflow: 'hidden',
        backgroundColor: '#000',
      }}
    >
      <style>{`
        div > pre {
          margin: 0;
          background: radial-gradient(circle at center, #0a1628 0%, #c4a882 100%) !important;
          -webkit-background-clip: text !important;
          background-clip: text !important;
          color: transparent !important;
          font-family: monospace;
          line-height: 1;
        }
      `}</style>
    </div>
  );
}
