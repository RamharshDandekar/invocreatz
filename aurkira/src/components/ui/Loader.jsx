import React from 'react';
import styled from 'styled-components';

const Loader = () => {
  return (
    <StyledWrapper>
      <div>
        <svg className="loader" viewBox="0 0 128 128" width="128px" height="128px" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <linearGradient id="grad1" x1={0} y1={0} x2={0} y2={1}>
              <stop offset="0%" stopColor="#000" />
              <stop offset="40%" stopColor="#fff" />
              <stop offset="100%" stopColor="#fff" />
            </linearGradient>
            <linearGradient id="grad2" x1={0} y1={0} x2={0} y2={1}>
              <stop offset="0%" stopColor="#000" />
              <stop offset="60%" stopColor="#000" />
              <stop offset="100%" stopColor="#fff" />
            </linearGradient>
            <mask id="mask1">
              <rect x={0} y={0} width={128} height={128} fill="url(#grad1)" />
            </mask>
            <mask id="mask2">
              <rect x={0} y={0} width={128} height={128} fill="url(#grad2)" />
            </mask>
          </defs>
          <g fill="none" strokeLinecap="round" strokeWidth={16}>
            <circle className="loader_ring" r={56} cx={64} cy={64} stroke="#ddd" />
            <g stroke="hsl(223,90%,50%)">
              <path className="loader_worm1" d="M120,64c0,30.928-25.072,56-56,56S8,94.928,8,64" stroke="hsl(343,90%,50%)" strokeDasharray="43.98 307.87" />
              <g transform="translate(42,42)">
                <g className="loader_worm2" transform="translate(-42,0)">
                  <path className="loader_worm2-1" d="M8,22c0-7.732,6.268-14,14-14s14,6.268,14,14" strokeDasharray="43.98 175.92" />
                </g>
              </g>
            </g>
            <g stroke="hsl(283,90%,50%)" mask="url(#mask1)">
              <path className="loader_worm1" d="M120,64c0,30.928-25.072,56-56,56S8,94.928,8,64" strokeDasharray="43.98 307.87" />
              <g transform="translate(42,42)">
                <g className="loader_worm2" transform="translate(-42,0)">
                  <path className="loader_worm2-1" d="M8,22c0-7.732,6.268-14,14-14s14,6.268,14,14" strokeDasharray="43.98 175.92" />
                </g>
              </g>
            </g>
            <g stroke="hsl(343,90%,50%)" mask="url(#mask2)">
              <path className="loader_worm1" d="M120,64c0,30.928-25.072,56-56,56S8,94.928,8,64" strokeDasharray="43.98 307.87" />
              <g transform="translate(42,42)">
                <g className="loader_worm2" transform="translate(-42,0)">
                  <path className="loader_worm2-1" d="M8,22c0-7.732,6.268-14,14-14s14,6.268,14,14" strokeDasharray="43.98 175.92" />
                </g>
              </g>
            </g>
          </g>
        </svg>
      </div>
    </StyledWrapper>
  );
}

const StyledWrapper = styled.div`
  .loader {
    display: block;
    width: 8em;
    height: 8em;
  }

  .loader_ring {
    stroke: hsla(var(--hue), 90%, 5%, 0.1);
    transition: stroke 0.3s;
  }

  .loader_worm1,
    .loader_worm2,
    .loader_worm2-1 {
    animation: worm1 5s ease-in infinite;
  }

  .loader_worm1 {
    transform-origin: 64px 64px;
  }

  .loader_worm2,
    .loader_worm2-1 {
    transform-origin: 22px 22px;
  }

  .loader_worm2 {
    animation-name: worm2;
    animation-timing-function: linear;
  }

  .loader_worm2-1 {
    animation-name: worm2-1;
    stroke-dashoffset: 175.92;
  }

    /* Dark theme */
  @media (prefers-color-scheme: dark) {
    :root {
      --bg: hsl(var(--hue), 90%, 5%);
      --fg: hsl(var(--hue), 90%, 95%);
    }

    .loader_ring {
      stroke: hsla(var(--hue), 90%, 95%, 0.1);
    }
  }

    /* Animations */
  @keyframes worm1 {
    from,
      to {
      stroke-dashoffset: 0;
    }

    12.5% {
      animation-timing-function: ease-out;
      stroke-dashoffset: -175.91;
    }

    25% {
      animation-timing-function: cubic-bezier(0, 0, 0.43, 1);
      stroke-dashoffset: -307.88;
    }

    50% {
      animation-timing-function: ease-in;
      stroke-dashoffset: -483.8;
    }

    62.5% {
      animation-timing-function: ease-out;
      stroke-dashoffset: -307.88;
    }

    75% {
      animation-timing-function: cubic-bezier(0, 0, 0.43, 1);
      stroke-dashoffset: -175.91;
    }
  }

  @keyframes worm2 {
    from,
      12.5%,
      75%,
      to {
      transform: rotate(0) translate(-42px, 0);
    }

    25%,
      62.5% {
      transform: rotate(0.5turn) translate(-42px, 0);
    }
  }

  @keyframes worm2-1 {
    from {
      stroke-dashoffset: 175.91;
      transform: rotate(0);
    }

    12.5% {
      animation-timing-function: cubic-bezier(0, 0, 0.42, 1);
      stroke-dashoffset: 0;
      transform: rotate(0);
    }

    25% {
      animation-timing-function: linear;
      stroke-dashoffset: 0;
      transform: rotate(1.5turn);
    }

    37.5%,
      50% {
      stroke-dashoffset: -175.91;
      transform: rotate(1.5turn);
    }

    62.5% {
      animation-timing-function: cubic-bezier(0, 0, 0.42, 1);
      stroke-dashoffset: 0;
      transform: rotate(1.5turn);
    }

    75% {
      animation-timing-function: linear;
      stroke-dashoffset: 0;
      transform: rotate(0);
    }

    87.5%,
      to {
      stroke-dashoffset: 175.92;
      transform: rotate(0);
    }
  }`;

export default Loader;
