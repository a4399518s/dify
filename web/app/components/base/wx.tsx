'use client';
import React from 'react';
import Script from 'next/script';
import { useEffect } from 'react';

declare global {
  namespace JSX {
    interface IntrinsicElements {
      'wx-open-subscribe': React.DetailedHTMLProps<React.HTMLAttributes<HTMLElement>, HTMLElement> & {
        template?: string;
        id?: string;
      };
    }
  }
}

export function WxSubscribeButton() {
  return (
    <>
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', width: '100%' , height: '50px' }}>
      <wx-open-subscribe
        // template="daRbCWvn3k2LDdWP6Atfm7CGYGuB-Zo87s6Ng2HrszM" // 美数合
        template="ryq4gI3ZZftKKXaxPShUYPS-ti1pb2g92k_BSYCZ9DQ" // 循圣堂
        id="subscribe-btn"
        style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', width: '100%' , height: '50px' }}
      >
        <script type="text/wxtag-template">
            <button
            style={{
              padding: '10px 20px',
              fontSize: '16px',
              backgroundColor: '#007BFF',
              color: 'white',
              border: 'none',
              borderRadius: '5px',
              cursor: 'pointer',
            }}
            >
            点击订阅视频通知
            </button>
        </script>
      </wx-open-subscribe>
      </div>
      {useEffect(() => {
        const btn = document.getElementById('subscribe-btn');
        if (btn) {
          btn.addEventListener('success', (e: Event) => {
            const detail = (e as CustomEvent).detail;
            console.log('success', detail);
            alert("订阅成功");
          });
          btn.addEventListener('error', (e: Event) => {
            const detail = (e as CustomEvent).detail;
            console.log('fail', detail);
            alert("fail" + detail.errMsg);
          });
        }
      }, [])}
    </>
  );
}
// const WxSubscribeButton: React.FC<WxSubscribeButtonProps> = ({ onClick, label = '订阅' }) => {
//   return (
//     <button
//       onClick={onClick}
//       className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600 focus:outline-none"
//     >
//       {label}
//     </button>
//   );
// };

// export default WxSubscribeButton;