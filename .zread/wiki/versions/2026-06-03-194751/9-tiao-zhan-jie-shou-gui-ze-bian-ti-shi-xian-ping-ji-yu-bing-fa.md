本页位于“基础配置”路径中的当前位置：[挑战接收规则：变体、时限、评级与并发](9-tiao-zhan-jie-shou-gui-ze-bian-ti-shi-xian-ping-ji-yu-bing-fa)。它只解释 `challenge` 配置如何决定**收到挑战后是否排队、拒绝、排序以及在并发容量内接受**，范围覆盖变体、时间控制、评级、机器人/真人策略、名单过滤与并发限制；引擎参数、开局库、聊天、主动配对和赛事配置分别属于后续页面。Sources: [config.yml.default](config.yml.default#L163-L213), [lichess_bot.py](lib/lichess_bot.py#L421-L452), [model.py](lib/model.py#L128-L158)

## 架构假设与验证结论

挑战接收链路可以从第一性原理拆成三个阶段：**建模**把 Lichess 事件转换为 `Challenge` 对象，**过滤**按 `challenge` 配置得到接受/拒绝结论，**调度**把可接受挑战放入队列并在 `concurrency` 容量允许时调用 Lichess 接受接口。代码验证显示，主循环在收到 `challenge` 事件时调用 `handle_challenge()`，后者构造 `model.Challenge`，刷新在线黑名单，调用 `Challenge.is_supported()`，通过后才进入 `challenge_queue` 并排序；随后主循环每轮调用 `accept_challenges()`，只要当前活跃对局数量小于 `challenge.concurrency` 就从队列取出挑战并接受。Sources: [lichess_bot.py](lib/lichess_bot.py#L477-L518), [lichess_bot.py](lib/lichess_bot.py#L604-L617), [lichess_bot.py](lib/lichess_bot.py#L730-L756), [model.py](lib/model.py#L25-L42)

```mermaid
flowchart TD
    A[Lichess control stream: challenge event] --> B[handle_challenge]
    B --> C[Challenge 模型提取 variant / speed / timeControl / challenger / rated]
    C --> D{is_supported 过滤链}
    D -- 不通过 --> E[decline_challenge(reason)]
    D -- 通过 --> F[加入 challenge_queue]
    F --> G[sort_challenges: best/first + human/bot preference]
    G --> H{len(active_games) < challenge.concurrency}
    H -- 是 --> I[accept_challenge]
    H -- 否 --> J[等待下一轮主循环容量释放]
    I --> K[active_games.add(challenge.id)]
```

从项目结构看，挑战接收配置并不分散在多个目录：默认配置在 `config.yml.default`，默认值与校验在 `lib/config.py`，领域判断在 `lib/model.py`，事件处理与并发调度在 `lib/lichess_bot.py`，额外自定义过滤入口在 `extra_game_handlers.py`。Sources: [config.yml.default](config.yml.default#L163-L213), [config.py](lib/config.py#L260-L279), [config.py](lib/config.py#L391-L409), [model.py](lib/model.py#L128-L158), [lichess_bot.py](lib/lichess_bot.py#L730-L756), [extra_game_handlers.py](extra_game_handlers.py#L15-L21)

```text
lichess-bot/
├── config.yml.default        # challenge: 默认挑战接收规则
├── extra_game_handlers.py    # is_supported_extra(): 配置之外的附加过滤
└── lib/
    ├── config.py             # challenge 默认值填充与合法性校验
    ├── model.py              # Challenge 对象与过滤规则
    └── lichess_bot.py        # 事件处理、挑战队列、并发接受
```

## `challenge` 配置块的职责边界

`challenge` 配置块只控制**外部用户向机器人发起挑战时**的处理策略，包括并发数量、队列排序、机器人/真人偏好、时限范围、变体白名单、rated/casual 模式、黑名单/白名单、评级范围、近期同一机器人挑战限制、bullet 是否要求增量，以及同一用户最大同时对局数。主动挑战其他机器人使用 `matchmaking` 配置，不属于本页；团队竞技场使用 `arena` 配置，也不属于本页。Sources: [config.yml.default](config.yml.default#L163-L213), [config.yml.default](config.yml.default#L236-L260), [config.yml.default](config.yml.default#L262-L316)

| 配置项 | 作用 | 默认示例或默认值来源 |
|---|---|---|
| `concurrency` | 机器人最多同时处理的非通信棋活跃对局数量 | 示例为 `1`，默认填充为 `1` |
| `sort_by` | 队列排序策略：`best` 或 `first` | 示例为 `best`，校验只允许 `best/first` |
| `preference` | 队列中偏好真人、机器人或无偏好 | 示例为 `none`，校验只允许 `none/human/bot` |
| `accept_bot` / `only_bot` | 是否接受机器人挑战，或是否只接受机器人挑战 | 示例为 `true/false`，默认填充为 `False/False` |
| `variants` | 允许的棋类变体列表 | 示例只启用 `standard` |
| `time_controls` | 允许的速度类别列表 | 示例启用 `bullet/blitz/rapid/classical` |
| `modes` | 允许 `casual`、`rated` 或两者 | 示例两者都允许 |
| `min_rating` / `max_rating` / `rating_difference` | 评级过滤区间与相对本机器人评级差 | 注释示例为 `0/4000/300`，默认为 `0/4000/None` |
| `max_simultaneous_games_per_user` | 同一用户同时对局/排队上限 | 示例与默认均为 `5` |

Sources: [config.yml.default](config.yml.default#L163-L213), [config.py](lib/config.py#L260-L279), [config.py](lib/config.py#L391-L409)

## 挑战对象如何被读取

收到挑战事件后，`Challenge.__init__()` 从 Lichess 数据中提取 `id`、`rated`、`variant.key`、`perf.name`、`speed`、`timeControl.limit`、`timeControl.increment`、`timeControl.daysPerTurn`、挑战者、目标用户、初始 FEN、颜色与完整 `timeControl`。这意味着后续所有过滤都基于事件中的标准字段，而不是重新查询单个挑战详情。Sources: [model.py](lib/model.py#L25-L42), [lichess_bot.py](lib/lichess_bot.py#L730-L735)

机器人会识别“自己发出的挑战”：如果挑战者名称等于当前机器人用户名，`from_self` 为真；这类挑战在 `is_supported()` 中直接通过，在 `handle_challenge()` 与 `accept_challenges()` 中也会被跳过或不再重复接受，用于避免把自己发出的挑战当作普通入站挑战处理。Sources: [model.py](lib/model.py#L35-L38), [model.py](lib/model.py#L132-L139), [lichess_bot.py](lib/lichess_bot.py#L734-L736), [lichess_bot.py](lib/lichess_bot.py#L607-L610)

## 变体过滤：`variants`

变体过滤由 `is_supported_variant()` 执行：挑战的 `variant` 必须出现在 `challenge.variants` 中；如果挑战带有非 `startpos` 的初始 FEN，代码会额外判断该 FEN 是否表示 Chess960，若是，则要求 `chess960` 也在允许变体列表中。Sources: [model.py](lib/model.py#L17-L19), [model.py](lib/model.py#L43-L55), [config.yml.default](config.yml.default#L176-L186)

| 想接受的挑战类型 | 配置要点 | 代码行为 |
|---|---|---|
| 标准国际象棋 | `variants: [standard]` | `variant == standard` 且在列表内即通过 |
| 指定局面但非 Chess960 | 需要相应 `variant` 在列表内 | 初始 FEN 不是 `startpos` 时仍可通过 |
| Chess960 初始局面 | `variants` 中需要包含 `chess960` | 非标准初始 FEN 被识别为 Chess960 时要求允许 `chess960` |
| Atomic、Crazyhouse 等 | 把对应 key 加入 `variants` | 仅按挑战中的 `variant.key` 与列表匹配 |

Sources: [config.yml.default](config.yml.default#L176-L186), [model.py](lib/model.py#L43-L55)

## 时限过滤：速度类别、基础时间、增量与通信棋

时间控制过滤由 `is_supported_time_control()` 执行，首先要求挑战的 `speed` 出现在 `challenge.time_controls` 中；随后实时棋检查 `limit` 与 `increment` 是否分别落在 `min_base/max_base` 和 `min_increment/max_increment` 范围内，通信棋检查 `daysPerTurn` 是否落在 `min_days/max_days` 范围内，无限时对局只有在 `max_days == math.inf` 时才会通过。Sources: [model.py](lib/model.py#L56-L84), [config.yml.default](config.yml.default#L169-L192)

| Lichess 时间形态 | Challenge 字段 | 过滤条件 |
|---|---|---|
| 实时棋，例如 bullet/blitz/rapid/classical | `timeControl.limit` + `timeControl.increment` | `speed` 在 `time_controls` 内，且基础时间与增量都在配置区间内 |
| 通信棋 | `timeControl.daysPerTurn` | `speed` 在 `time_controls` 内，且每步天数在 `min_days/max_days` 内 |
| 无限时 | 无 `limit/increment/daysPerTurn` | 只有 `max_days` 为无穷大时通过 |

Sources: [model.py](lib/model.py#L66-L84), [config.yml.default](config.yml.default#L169-L175), [config.py](lib/config.py#L265-L270)

`bullet_requires_increment` 是一个针对机器人对手的附加保护：当挑战者是 BOT、速度为 `bullet`，且该选项为真时，最小增量会被提升到至少 `1` 秒；因此即使 `min_increment: 0`，来自 BOT 的无增量 bullet 挑战也不会通过。Sources: [model.py](lib/model.py#L69-L77), [config.yml.default](config.yml.default#L211-L212)

配置校验不会强制阻止所有不合理区间，但会发出警告：如果 `min_increment > max_increment` 或 `min_base > max_base`，实时棋挑战不会被接受；如果 `min_days > max_days`，通信棋挑战不会被接受。Sources: [config.py](lib/config.py#L398-L403)

## Rated / Casual 模式过滤

模式过滤由 `is_supported_mode()` 执行：如果挑战是 rated，就要求 `rated` 出现在 `challenge.modes`；如果挑战是非 rated，就要求 `casual` 出现在 `challenge.modes`。拒绝原因会根据当前挑战类型反向设置：不接受 rated 时返回 `casual`，不接受 casual 时返回 `rated`，这是 Lichess decline reason 的实现细节。Sources: [model.py](lib/model.py#L85-L88), [model.py](lib/model.py#L144-L149), [config.yml.default](config.yml.default#L193-L195)

| `modes` 配置 | 接受 rated | 接受 casual |
|---|---:|---:|
| `['casual', 'rated']` | 是 | 是 |
| `['casual']` | 否 | 是 |
| `['rated']` | 是 | 否 |

Sources: [config.yml.default](config.yml.default#L193-L195), [model.py](lib/model.py#L85-L88)

## 评级过滤：绝对区间与相对差值

评级过滤由 `is_supported_rating()` 执行：如果挑战者没有评级，例如 AI 对手，直接通过；否则先读取 `min_rating` 与 `max_rating`，再在 `rating_difference` 不为 `None` 且机器人当前对应 perf 有 rating 时，把允许区间收窄到“机器人 rating ± rating_difference”与原始上下限的交集。Sources: [model.py](lib/model.py#L89-L105), [test_model.py](test_bot/test_model.py#L70-L138)

| 配置组合 | 实际含义 |
|---|---|
| `min_rating: 0`, `max_rating: 4000`, `rating_difference: null` | 接受 Lichess 常见评级范围内的所有有评级挑战者 |
| `min_rating: 1800`, `max_rating: 2400` | 只接受绝对评级在 1800 到 2400 之间的挑战者 |
| `rating_difference: 300` | 若机器人对应速度 rating 为 2500，则允许范围被收窄到最多 2200–2800，并仍受 `min_rating/max_rating` 限制 |
| 挑战者无 rating | 评级过滤直接通过 |

Sources: [model.py](lib/model.py#L91-L105), [config.yml.default](config.yml.default#L208-L210), [test_model.py](test_bot/test_model.py#L113-L138)

配置校验会在 `min_rating > max_rating` 时警告“不会接受挑战”，并在 `rating_difference < 0` 时警告“不会接受挑战”；这两个场景不是正常的容量调优手段，而是应修复的配置错误。Sources: [config.py](lib/config.py#L405-L409)

## 真人、机器人、白名单与黑名单

机器人/真人过滤位于 `is_supported()` 的过滤链前段：`accept_bot` 为假时会拒绝 BOT 挑战，`only_bot` 为真时会拒绝非 BOT 挑战；`Player` 模型把 `title == "BOT"` 或存在 `aiLevel` 的挑战者视为 bot。Sources: [model.py](lib/model.py#L143-L146), [model.py](lib/model.py#L316-L323), [config.yml.default](config.yml.default#L167-L168)

名单过滤按顺序参与同一条过滤链：本地 `block_list`、在线 `online_block_list` 命中会拒绝；`allow_list` 非空时，只接受名单中的挑战者；如果 `allow_list` 为空，代码会把当前挑战者自身作为允许对象，因此默认并不会限制挑战者来源。Sources: [model.py](lib/model.py#L143-L156), [config.yml.default](config.yml.default#L196-L203), [lichess_bot.py](lib/lichess_bot.py#L738-L748)

`always_allow_users` 是更强的信任名单：挑战者名称大小写折叠后命中该列表时，`is_supported()` 直接返回通过，绕过后续普通入站挑战过滤，例如评级过滤；测试用例验证了该名单可以让低于 `min_rating` 的指定用户仍被接受。Sources: [model.py](lib/model.py#L136-L139), [config.yml.default](config.yml.default#L204-L205), [test_model.py](test_bot/test_model.py#L141-L170)

## 同一机器人近期挑战与同一用户并发限制

`recent_bot_challenge_age` 与 `max_recent_bot_challenges` 只针对 BOT 挑战者：机器人会为每个 BOT 挑战者保存一组带过期时间的 `Timer`，过滤时先移除过期记录，再检查近期挑战数量是否低于上限；挑战通过并入队后，会按 `recent_bot_challenge_age` 追加一条近期记录。Sources: [model.py](lib/model.py#L107-L117), [lichess_bot.py](lib/lichess_bot.py#L748-L755), [config.yml.default](config.yml.default#L206-L207)

`max_simultaneous_games_per_user` 控制同一用户的同时参与数：`handle_challenge()` 会统计当前 Lichess 进行中对局的对手用户名，并把队列中尚未接受的挑战者也计入 `opponent_engagements`；随后 `is_supported()` 要求该用户计数小于配置上限，否则以 `later` 拒绝。Sources: [lichess_bot.py](lib/lichess_bot.py#L738-L740), [model.py](lib/model.py#L153-L155), [config.yml.default](config.yml.default#L212-L213)

## 队列排序：`sort_by` 与 `preference`

挑战通过过滤后先进入 `challenge_queue`，再由 `sort_challenges()` 排序。`sort_by: best` 会按 `Challenge.score()` 从高到低排序；分数等于挑战者 rating，加上 rated 挑战奖励 200 分，再加上非 BOT 有头衔挑战者奖励 200 分。`sort_by: first` 不触发评分排序，保留先入队者优先。Sources: [lichess_bot.py](lib/lichess_bot.py#L634-L647), [model.py](lib/model.py#L164-L170), [config.py](lib/config.py#L394-L396)

`preference` 会在评分排序之后再次排序：当值为 `bot` 时，BOT 挑战者被排到前面；当值为 `human` 时，非 BOT 挑战者被排到前面；当值为 `none` 时不做这一步。由于 Python 排序稳定，第二次排序会按人机偏好分组，同时保留组内前一步形成的相对顺序。Sources: [lichess_bot.py](lib/lichess_bot.py#L642-L647), [config.yml.default](config.yml.default#L164-L168), [config.py](lib/config.py#L394-L396)

| `sort_by` | `preference` | 队列效果 |
|---|---|---|
| `best` | `none` | 评级、rated、头衔综合分最高者优先 |
| `first` | `none` | 先通过过滤并入队者优先 |
| `best` | `human` | 真人优先；真人组内仍按 `best` 结果排序 |
| `best` | `bot` | BOT 优先；BOT 组内仍按 `best` 结果排序 |

Sources: [lichess_bot.py](lib/lichess_bot.py#L634-L647), [model.py](lib/model.py#L164-L170)

## 全局并发：`concurrency`

主循环把 `max_games` 设置为 `config.challenge.concurrency`，并用它创建大小为 `max_games + 1` 的进程池；接受挑战时，`accept_challenges()` 只有在 `len(active_games) < max_games` 时才会弹出队列并调用 `li.accept_challenge()`，接受后立即把挑战 id 加入 `active_games`。Sources: [lichess_bot.py](lib/lichess_bot.py#L421-L456), [lichess_bot.py](lib/lichess_bot.py#L604-L617)

`active_games` 在启动时来自 Lichess 当前进行中对局，但启动时的通信棋会被排除到 `startup_correspondence_games`，非通信棋进入 `active_games`；对局结束、本地完成或挑战取消时，主循环会从 `active_games`、`started_games`、`pending_games` 中移除对应 id，从而释放容量。Sources: [lichess_bot.py](lib/lichess_bot.py#L425-L435), [lichess_bot.py](lib/lichess_bot.py#L470-L493)

如果 `challenge.concurrency` 设置为 `0`，配置校验会发出警告：机器人不会接受或创建任何挑战。这个行为来自容量判断本身，因为 `len(active_games) < 0` 永远不成立，`len(active_games) < max_games` 在 `max_games == 0` 时也不会为真。Sources: [config.py](lib/config.py#L391-L392), [lichess_bot.py](lib/lichess_bot.py#L604-L617)

## 过滤链的拒绝原因

`Challenge.is_supported()` 用一条短路链生成拒绝原因：从机器人/真人策略、时限、变体、模式、评级、黑名单、白名单、近期 BOT 挑战、同用户并发，到 `extra_game_handlers.is_supported_extra()`，第一个不满足的条件决定最终拒绝原因；如果没有拒绝原因，则返回 `(True, "")`。Sources: [model.py](lib/model.py#L128-L158), [extra_game_handlers.py](extra_game_handlers.py#L15-L21)

| 过滤条件 | 不通过时的 decline reason |
|---|---|
| 不接受 BOT | `noBot` |
| 只接受 BOT，但挑战者不是 BOT | `onlyBot` |
| 时间控制不匹配 | `timeControl` |
| 变体不匹配 | `variant` |
| rated/casual 模式不匹配 | `casual` 或 `rated` |
| 评级、名单、自定义附加规则等通用限制 | `generic` |
| 近期 BOT 挑战过多或同用户并发过多 | `later` |

Sources: [model.py](lib/model.py#L143-L156)

## 推荐配置片段

如果你希望机器人只接受标准棋、实时短时限、rated/casual 都允许、最多同时两盘，并避免同一用户刷满容量，可以把 `challenge` 调整为类似下面的结构；字段名称与默认文件一致，具体数值应按你的引擎强度与机器资源设置。Sources: [config.yml.default](config.yml.default#L163-L213), [lichess_bot.py](lib/lichess_bot.py#L604-L617)

```yaml
challenge:
  concurrency: 2
  sort_by: "best"
  preference: "none"
  accept_bot: true
  only_bot: false

  min_increment: 0
  max_increment: 10
  min_base: 60
  max_base: 600
  min_days: 1
  max_days: 14

  variants:
    - standard

  time_controls:
    - bullet
    - blitz
    - rapid

  modes:
    - casual
    - rated

  min_rating: 1200
  max_rating: 2600
  rating_difference: 400

  bullet_requires_increment: true
  max_simultaneous_games_per_user: 2
```

如果你更关注公平排队而不是强度优先，把 `sort_by` 改为 `first`；如果你只希望与真人下棋，把 `accept_bot` 设为 `false` 且保持 `only_bot: false`；如果你只希望与机器人测试，把 `accept_bot: true` 与 `only_bot: true` 组合使用。Sources: [config.yml.default](config.yml.default#L164-L168), [config.py](lib/config.py#L263-L264), [lichess_bot.py](lib/lichess_bot.py#L634-L647), [model.py](lib/model.py#L143-L146)

## 排查表

当挑战被拒绝时，优先按过滤链顺序排查，因为代码会采用第一个失败条件作为拒绝原因；例如同时存在时限不匹配与变体不匹配时，`timeControl` 会先于 `variant` 返回。Sources: [model.py](lib/model.py#L143-L158)

| 现象 | 首要检查项 | 依据 |
|---|---|---|
| 收到 `timeControl` 拒绝 | `time_controls`、`min_base/max_base`、`min_increment/max_increment`、`min_days/max_days` | 时间控制先检查 speed，再检查实时棋或通信棋范围 |
| 收到 `variant` 拒绝 | `variants` 是否包含挑战的 `variant.key`；Chess960 初始局面是否允许 `chess960` | 变体列表与 Chess960 FEN 特判共同决定 |
| rated 挑战被拒绝 | `modes` 是否包含 `rated` | 模式过滤按挑战 rated 布尔值映射 |
| BOT 挑战被拒绝 | `accept_bot`、`only_bot`、`bullet_requires_increment`、近期 BOT 限制 | BOT 会经过专门策略与近期挑战限制 |
| 队列中有挑战但不接受 | `concurrency` 与当前 `active_games` 数量 | 只有活跃对局数小于并发上限才接受 |
| 某用户后续挑战被 `later` 拒绝 | `max_simultaneous_games_per_user` 或 `max_recent_bot_challenges` | 同用户进行中对局与队列挑战都会计数 |

Sources: [model.py](lib/model.py#L56-L84), [model.py](lib/model.py#L107-L117), [model.py](lib/model.py#L143-L156), [lichess_bot.py](lib/lichess_bot.py#L604-L617), [lichess_bot.py](lib/lichess_bot.py#L738-L740)

## 下一步阅读

完成本页后，建议继续阅读 [开局库、在线走法与残局库配置](10-kai-ju-ku-zai-xian-zou-fa-yu-can-ju-ku-pei-zhi)，因为挑战被接受后，实际走法来源将由引擎、开局库、在线分析和残局库配置决定；如果你要调整认输、求和、悔棋或聊天行为，请转到 [认输、求和、悔棋与聊天行为配置](11-ren-shu-qiu-he-hui-qi-yu-liao-tian-xing-wei-pei-zhi)。Sources: [config.yml.default](config.yml.default#L16-L30), [config.yml.default](config.yml.default#L59-L68), [config.yml.default](config.yml.default#L214-L222)

如果你的目标不是被动接收挑战，而是让机器人主动寻找其他 BOT 对局，请阅读 [启用主动配对并挑战其他机器人](12-qi-yong-zhu-dong-pei-dui-bing-tiao-zhan-qi-ta-ji-qi-ren)；如果你需要理解挑战事件如何进入主循环并与多进程游戏 worker 协作，请阅读 [主循环、事件流与多进程任务协作](17-zhu-xun-huan-shi-jian-liu-yu-duo-jin-cheng-ren-wu-xie-zuo)。Sources: [config.yml.default](config.yml.default#L262-L316), [lichess_bot.py](lib/lichess_bot.py#L395-L525)