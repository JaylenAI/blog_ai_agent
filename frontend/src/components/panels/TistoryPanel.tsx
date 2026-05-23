export function TistoryPanel() {
  return (
    <div className="sb-panel-info">
      <div className="sb-panel-info-row">
        <span className="sb-panel-info-label">블로그</span>
        <span>jaylenhan.tistory.com</span>
      </div>
      <div className="sb-panel-info-row">
        <span className="sb-panel-info-label">연결 방식</span>
        <span>Playwright (수동 로그인)</span>
      </div>
      <p className="sb-panel-note">
        Tistory 발행은 Gate 2 승인 후 Playwright가 브라우저를 열어
        진행합니다. 카카오 로그인이 필요할 경우 수동으로 진행해 주세요.
      </p>
    </div>
  );
}
