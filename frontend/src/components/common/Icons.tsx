interface IconProps {
  s?: number;
  w?: number;
  className?: string;
}

function Ic({
  d,
  s = 16,
  fill = "none",
  stroke = "currentColor",
  w = 1.5,
  className,
}: {
  d: React.ReactNode;
  s?: number;
  fill?: string;
  stroke?: string;
  w?: number;
  className?: string;
}) {
  return (
    <svg
      width={s}
      height={s}
      viewBox="0 0 16 16"
      fill={fill}
      stroke={stroke}
      strokeWidth={w}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
    >
      {d}
    </svg>
  );
}

export const Icons = {
  Chevron: (p: IconProps) => (
    <Ic {...p} d={<polyline points="6 4 10 8 6 12" />} />
  ),
  Plus: (p: IconProps) => (
    <Ic
      {...p}
      d={
        <>
          <line x1="8" y1="3" x2="8" y2="13" />
          <line x1="3" y1="8" x2="13" y2="8" />
        </>
      }
    />
  ),
  Search: (p: IconProps) => (
    <Ic
      {...p}
      d={
        <>
          <circle cx="7" cy="7" r="4" />
          <line x1="13" y1="13" x2="10" y2="10" />
        </>
      }
    />
  ),
  Doc: (p: IconProps) => (
    <Ic
      {...p}
      d={
        <>
          <path d="M4 2h5l3 3v9H4z" />
          <polyline points="9 2 9 5 12 5" />
        </>
      }
    />
  ),
  Folder: (p: IconProps) => (
    <Ic {...p} d={<path d="M2 4h4l1.5 1.5H14V13H2z" />} />
  ),
  Inbox: (p: IconProps) => (
    <Ic
      {...p}
      d={
        <>
          <path d="M2 9h3l1 2h4l1-2h3" />
          <path d="M2 9V4h12v5v4H2z" />
        </>
      }
    />
  ),
  Send: (p: IconProps) => (
    <Ic
      {...p}
      d={
        <>
          <polygon points="2 8 14 2 13 14 8 9" />
          <line x1="8" y1="9" x2="14" y2="2" />
        </>
      }
    />
  ),
  Cog: (p: IconProps) => (
    <Ic
      {...p}
      d={
        <>
          <circle cx="8" cy="8" r="2.2" />
          <path d="M8 1v2M8 13v2M1 8h2M13 8h2M3 3l1.5 1.5M11.5 11.5L13 13M3 13l1.5-1.5M11.5 4.5L13 3" />
        </>
      }
    />
  ),
  Beaker: (p: IconProps) => (
    <Ic
      {...p}
      d={
        <>
          <path d="M6 2v4L3 12a1 1 0 0 0 1 1.5h8a1 1 0 0 0 1-1.5l-3-6V2" />
          <line x1="5" y1="2" x2="11" y2="2" />
        </>
      }
    />
  ),
  Sparkle: (p: IconProps) => (
    <Ic
      {...p}
      d={<path d="M8 1l1.6 4.4L14 7l-4.4 1.6L8 13l-1.6-4.4L2 7l4.4-1.6z" />}
    />
  ),
  Bot: (p: IconProps) => (
    <Ic
      {...p}
      d={
        <>
          <rect x="3" y="5" width="10" height="8" rx="1.5" />
          <line x1="8" y1="2" x2="8" y2="5" />
          <circle cx="6" cy="9" r="0.5" fill="currentColor" />
          <circle cx="10" cy="9" r="0.5" fill="currentColor" />
        </>
      }
    />
  ),
  Eye: (p: IconProps) => (
    <Ic
      {...p}
      d={
        <>
          <path d="M1 8s2.5-5 7-5 7 5 7 5-2.5 5-7 5S1 8 1 8z" />
          <circle cx="8" cy="8" r="2" />
        </>
      }
    />
  ),
  Share: (p: IconProps) => (
    <Ic
      {...p}
      d={
        <>
          <circle cx="12" cy="3" r="1.5" />
          <circle cx="4" cy="8" r="1.5" />
          <circle cx="12" cy="13" r="1.5" />
          <line x1="5.5" y1="7" x2="10.5" y2="4" />
          <line x1="5.5" y1="9" x2="10.5" y2="12" />
        </>
      }
    />
  ),
  Check: (p: IconProps) => (
    <Ic {...p} d={<polyline points="3 8 7 12 13 4" />} />
  ),
  X: (p: IconProps) => (
    <Ic
      {...p}
      d={
        <>
          <line x1="4" y1="4" x2="12" y2="12" />
          <line x1="12" y1="4" x2="4" y2="12" />
        </>
      }
    />
  ),
  Sidebar: (p: IconProps) => (
    <Ic
      {...p}
      d={
        <>
          <rect x="2" y="3" width="12" height="10" rx="1" />
          <line x1="6" y1="3" x2="6" y2="13" />
        </>
      }
    />
  ),
  More: (p: IconProps) => (
    <Ic
      {...p}
      d={
        <>
          <circle cx="4" cy="8" r="0.8" fill="currentColor" />
          <circle cx="8" cy="8" r="0.8" fill="currentColor" />
          <circle cx="12" cy="8" r="0.8" fill="currentColor" />
        </>
      }
    />
  ),
  Globe: (p: IconProps) => (
    <Ic
      {...p}
      d={
        <>
          <circle cx="8" cy="8" r="6" />
          <line x1="2" y1="8" x2="14" y2="8" />
          <path d="M8 2c2 2 2 10 0 12M8 2c-2 2-2 10 0 12" />
        </>
      }
    />
  ),
  Hash: (p: IconProps) => (
    <Ic
      {...p}
      d={
        <>
          <line x1="3" y1="6" x2="13" y2="6" />
          <line x1="3" y1="10" x2="13" y2="10" />
          <line x1="6" y1="3" x2="5" y2="13" />
          <line x1="11" y1="3" x2="10" y2="13" />
        </>
      }
    />
  ),
  Layers: (p: IconProps) => (
    <Ic
      {...p}
      d={
        <>
          <polygon points="8 2 14 5 8 8 2 5" />
          <polyline points="2 8 8 11 14 8" />
          <polyline points="2 11 8 14 14 11" />
        </>
      }
    />
  ),
  CheckCircle: (p: IconProps) => (
    <Ic
      {...p}
      d={
        <>
          <circle cx="8" cy="8" r="6" />
          <polyline points="5 8 7 10 11 6" />
        </>
      }
    />
  ),
  Lock: (p: IconProps) => (
    <Ic
      {...p}
      d={
        <>
          <rect x="3" y="7" width="10" height="7" rx="1" />
          <path d="M5 7V5a3 3 0 1 1 6 0v2" />
        </>
      }
    />
  ),
  Tag: (p: IconProps) => (
    <Ic
      {...p}
      d={
        <>
          <path d="M2 8V2h6l6 6-6 6z" />
          <circle cx="5" cy="5" r="0.8" fill="currentColor" />
        </>
      }
    />
  ),
  Moon: (p: IconProps) => (
    <Ic
      {...p}
      d={<path d="M13 8.5A5.5 5.5 0 1 1 7.5 3 4 4 0 0 0 13 8.5z" />}
    />
  ),
  Sun: (p: IconProps) => (
    <Ic
      {...p}
      d={
        <>
          <circle cx="8" cy="8" r="3" />
          <path d="M8 1v2M8 13v2M1 8h2M13 8h2M3.5 3.5l1.4 1.4M11.1 11.1l1.4 1.4M3.5 12.5l1.4-1.4M11.1 4.9l1.4-1.4" />
        </>
      }
    />
  ),
  ExternalLink: (p: IconProps) => (
    <Ic {...p} d={<path d="M11 1h4v4M15 1L8 8M13 9v4a1 1 0 01-1 1H3a1 1 0 01-1-1V5a1 1 0 011-1h4" />} />
  ),
};
