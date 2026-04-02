import nextConfig from "eslint-config-next";
import nextCoreWebVitals from "eslint-config-next/core-web-vitals";

const eslintConfig = [
  ...nextConfig,
  ...nextCoreWebVitals,
  {
    rules: {
      // react-hooks 7.x で追加された新ルール。既存の非同期フェッチパターンと競合するため
      // 個別の修正は別Issueで対応する（#72の範囲外）
      "react-hooks/set-state-in-effect": "off",
    },
  },
];

export default eslintConfig;
