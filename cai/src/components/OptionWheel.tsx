import { useCallback, useRef } from 'react';
import { LayoutDashboard, Upload, FileCheck, DollarSign } from 'lucide-react';

interface OptionWheelProps {
  items: string[];
  activeIndex: number;
  onSelect: (index: number) => void;
}

const icons = [LayoutDashboard, Upload, FileCheck, DollarSign];

export default function OptionWheel({ items, activeIndex, onSelect }: OptionWheelProps) {
  const audioCtxRef = useRef<AudioContext | null>(null);

  // Play subtle mechanical click sound
  const playClick = useCallback(() => {
    try {
      if (!audioCtxRef.current) {
        audioCtxRef.current = new (window.AudioContext || (window as any).webkitAudioContext)();
      }
      const ctx = audioCtxRef.current;
      if (ctx.state === 'suspended') {
        ctx.resume();
      }
      
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      
      osc.type = 'sine';
      osc.frequency.setValueAtTime(800, ctx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(300, ctx.currentTime + 0.03);
      
      gain.gain.setValueAtTime(0.03, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.03);
      
      osc.connect(gain);
      gain.connect(ctx.destination);
      
      osc.start();
      osc.stop(ctx.currentTime + 0.03);
    } catch (e) {
      // Ignore audio policy errors
    }
  }, []);

  const handleItemClick = (index: number) => {
    playClick();
    onSelect(index);
  };

  if (items.length === 0) {
    return <></>;
  }

  return (
    <nav className="fixed left-20 top-[40%] -translate-y-1/2 flex flex-col items-start select-none z-50">
      <div className="glass-ios-subtle p-3 rounded-2xl flex flex-col space-y-1.5 backdrop-blur-xl border border-white/10 shadow-2xl">
        {items.map((item, index) => {
          const isActive = index === activeIndex;
          const Icon = icons[index % icons.length] || LayoutDashboard;

          return (
            <button
              key={item}
              onClick={() => handleItemClick(index)}
              onMouseEnter={playClick}
              className={`flex items-center space-x-4 px-5 py-3 rounded-xl text-sm font-medium transition-all duration-200 w-52 text-left group ${
                isActive
                  ? 'bg-[var(--color-beige)]/15 text-[var(--color-beige)] border border-[var(--color-beige)]/30 shadow-[0_0_15px_rgba(196,168,130,0.15)] font-semibold'
                  : 'text-[var(--color-slate)] hover:text-white hover:bg-white/5 border border-transparent'
              }`}
            >
              <Icon className={`w-5 h-5 transition-transform group-hover:scale-110 ${isActive ? 'text-[var(--color-beige)]' : 'text-[var(--color-slate)] group-hover:text-white'}`} />
              <span className="truncate">{item}</span>
              {isActive && (
                <span className="ml-auto w-1.5 h-1.5 rounded-full bg-[var(--color-beige)] shadow-[0_0_8px_#c4a882]" />
              )}
            </button>
          );
        })}
      </div>
    </nav>
  );
}
