"use client";

import Script from "next/script";

export default function SplineViewerClient() {
    return (
        <>
            <Script
                type="module"
                src="https://unpkg.com/@splinetool/viewer@1.12.60/build/spline-viewer.js"
                strategy="lazyOnload"
            />
            <div
                className="absolute inset-0 z-0 pointer-events-none"
                dangerouslySetInnerHTML={{
                    __html: '<spline-viewer url="https://prod.spline.design/qwXYdfDuVtIZ2NZZ/scene.splinecode"></spline-viewer>'
                }}
            />
        </>
    );
}
