// File: src/types/qrcode.d.ts

declare module 'qrcode.react' {
    import * as React from 'react';
  
    export interface QRCodeProps {
      value: string;
      size?: number;
      level?: 'L' | 'M' | 'Q' | 'H';
      bgColor?: string;
      fgColor?: string;
      includeMargin?: boolean;
      style?: React.CSSProperties;
      className?: string;
    }
    
    // Legacy default export (deprecated but still used in some projects)
    const QRCode: React.FC<QRCodeProps>;
    export default QRCode;
    
    // Modern named exports (recommended)
    export const QRCodeSVG: React.FC<QRCodeProps>;
    export const QRCodeCanvas: React.FC<QRCodeProps>;
  }