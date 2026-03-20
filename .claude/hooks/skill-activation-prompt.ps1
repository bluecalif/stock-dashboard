$ErrorActionPreference = "SilentlyContinue"

Push-Location $PSScriptRoot
try {
    $stdinContent = [Console]::In.ReadToEnd()
    $stdinContent | npx tsx skill-activation-prompt.ts 2>$null
} catch {
    # Hook 에러는 채팅 흐름을 방해하지 않도록 조용히 종료
} finally {
    Pop-Location
}
exit 0
