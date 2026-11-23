import os
from render_vscode_screenshots import generate_vscode_shot

out_dir = r"D:\hdv\backend\docs\diagrams"

# 1. Auth Guard
lines_guard = [
    '<span class="dec">@Injectable</span>()',
    '<span class="kw">export class</span> <span class="type">AuthGuard</span> <span class="kw">implements</span> <span class="type">CanActivate</span> {',
    '  <span class="kw">constructor</span>(<span class="kw">private readonly</span> <span class="prop">reflector</span>: <span class="type">Reflector</span>, <span class="kw">private readonly</span> <span class="prop">db</span>: <span class="type">Database</span>) {}',
    '  <span class="kw">async</span> <span class="fn">canActivate</span>(<span class="prop">ctx</span>: <span class="type">ExecutionContext</span>) {',
    '    <span class="kw-ctrl">if</span> (<span class="kw">this</span>.<span class="prop">reflector</span>.<span class="fn">getAllAndOverride</span>&lt;<span class="type">boolean</span>&gt;(<span class="str">\'public\'</span>, [<span class="prop">ctx</span>.<span class="fn">getHandler</span>(), <span class="prop">ctx</span>.<span class="fn">getClass</span>()])) <span class="kw-ctrl">return</span> <span class="kw">true</span>;',
    '    <span class="kw">const</span> <span class="prop">req</span> = <span class="prop">ctx</span>.<span class="fn">switchToHttp</span>().<span class="fn">getRequest</span>&lt;<span class="type">AuthRequest</span>&gt;();',
    '    <span class="kw">const</span> <span class="prop">header</span> = <span class="prop">req</span>.<span class="prop">headers</span>.<span class="prop">authorization</span>;',
    '    <span class="kw-ctrl">if</span> (!<span class="prop">header</span>?.<span class="fn">startsWith</span>(<span class="str">\'Bearer \'</span>)) <span class="kw-ctrl">throw new</span> <span class="type">ApiError</span>(<span class="str">\'UNAUTHORIZED\'</span>, <span class="str">\'Authentication required\'</span>, <span class="num">401</span>);',
    '    <span class="kw">let</span> <span class="prop">principal</span>: <span class="type">Principal</span>;',
    '    <span class="kw-ctrl">try</span> { <span class="prop">principal</span> = <span class="kw">await</span> <span class="fn">verifyAccess</span>(<span class="prop">header</span>.<span class="fn">slice</span>(<span class="num">7</span>), <span class="fn">loadConfig</span>().<span class="prop">jwtSecret</span>); }',
    '    <span class="kw-ctrl">catch</span> { <span class="kw-ctrl">throw new</span> <span class="type">ApiError</span>(<span class="str">\'UNAUTHORIZED\'</span>, <span class="str">\'Invalid or expired access token\'</span>, <span class="num">401</span>); }',
    '    <span class="cm">// Kiểm tra phiên refresh_sessions và trạng thái ACTIVE trong PostgreSQL</span>',
    '    <span class="kw">const</span> <span class="prop">session</span> = <span class="kw">await</span> <span class="kw">this</span>.<span class="prop">db</span>.<span class="fn">query</span>(<span class="str">`SELECT 1 FROM identity.refresh_sessions s JOIN identity.users u ON u.id=s.user_id',
    '      WHERE s.id=$1 AND s.user_id=$2 AND s.revoked_at IS NULL AND s.expires_at>now() AND u.status=\'ACTIVE\'`</span>, [<span class="prop">principal</span>.<span class="prop">sessionId</span>, <span class="prop">principal</span>.<span class="prop">userId</span>]);',
    '    <span class="kw-ctrl">if</span> (!<span class="prop">session</span>.<span class="prop">rowCount</span>) <span class="kw-ctrl">throw new</span> <span class="type">ApiError</span>(<span class="str">\'UNAUTHORIZED\'</span>, <span class="str">\'Session has been revoked\'</span>, <span class="num">401</span>);',
    '    <span class="prop">req</span>.<span class="prop">principal</span> = <span class="prop">principal</span>;',
    '    <span class="kw-ctrl">return</span> <span class="kw">true</span>;',
    '  }',
    '}'
]

generate_vscode_shot(
    os.path.join(out_dir, "shot_auth_guard.html"),
    os.path.join(out_dir, "vscode_auth_guard.png"),
    "guard.ts - packages/auth - Anta Backend",
    "guard.ts",
    "packages > auth",
    "AuthGuard > canActivate",
    "TypeScript",
    "TS",
    "",
    11,
    lines_guard
)

# 2. Access Service
lines_access = [
    '<span class="dec">@Injectable</span>()',
    '<span class="kw">export class</span> <span class="type">AccessService</span> {',
    '  <span class="kw">constructor</span>(<span class="kw">private readonly</span> <span class="prop">db</span>: <span class="type">Database</span>) {}',
    '  <span class="cm">// Kiểm tra quyền Chủ chi nhánh sân (branch_owner)</span>',
    '  <span class="kw">async</span> <span class="fn">owner</span>(<span class="prop">userId</span>: <span class="type">string</span>, <span class="prop">branchId</span>: <span class="type">string</span>, <span class="prop">tx</span>: <span class="type">DbClient</span> = <span class="kw">this</span>.<span class="prop">db</span>.<span class="prop">pool</span>) {',
    '    <span class="kw">const</span> <span class="prop">allowed</span> = <span class="kw">await</span> <span class="prop">tx</span>.<span class="fn">query</span>(<span class="str">`SELECT 1 FROM identity.roles WHERE user_id=$1',
    '      AND (role=\'admin\' OR (branch_id=$2 AND role=\'branch_owner\')) LIMIT 1`</span>, [<span class="prop">userId</span>, <span class="prop">branchId</span>]);',
    '    <span class="fn">invariant</span>(<span class="prop">allowed</span>.<span class="prop">rowCount</span>, <span class="str">\'FORBIDDEN\'</span>, <span class="str">\'Branch owner permission required\'</span>, <span class="num">403</span>);',
    '  }',
    '  <span class="cm">// Kiểm tra quyền Quản trị viên toàn hệ thống (admin)</span>',
    '  <span class="kw">async</span> <span class="fn">admin</span>(<span class="prop">userId</span>: <span class="type">string</span>, <span class="prop">tx</span>: <span class="type">DbClient</span> = <span class="kw">this</span>.<span class="prop">db</span>.<span class="prop">pool</span>) {',
    '    <span class="kw">const</span> <span class="prop">allowed</span> = <span class="kw">await</span> <span class="prop">tx</span>.<span class="fn">query</span>(<span class="str">"SELECT 1 FROM identity.roles WHERE user_id=$1 AND role=\'admin\' LIMIT 1"</span>, [<span class="prop">userId</span>]);',
    '    <span class="fn">invariant</span>(<span class="prop">allowed</span>.<span class="prop">rowCount</span>, <span class="str">\'FORBIDDEN\'</span>, <span class="str">\'Admin permission required\'</span>, <span class="num">403</span>);',
    '  }',
    '}'
]

generate_vscode_shot(
    os.path.join(out_dir, "shot_access_service.html"),
    os.path.join(out_dir, "vscode_access_service.png"),
    "access.ts - packages - Anta Backend",
    "access.ts",
    "packages",
    "AccessService",
    "TypeScript",
    "TS",
    "",
    5,
    lines_access
)

print("Auth & Access screenshots generated successfully!")

