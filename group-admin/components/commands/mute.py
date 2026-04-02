from langbot_plugin.api.definition.component import Command
from langbot_plugin.api.entities.builtin.pipeline import context
from langbot_plugin.api.entities.builtin.platform import message as platform_message


class MuteCommand(Command):

    async def initialize(self):
        pass

    async def execute(self, event_context: context.EventContext, args: list):
        event = event_context.event
        sender_id = str(event.sender_id)

        if not self.plugin.is_admin(sender_id):
            await event_context.reply(
                platform_message.MessageChain(
                    [platform_message.Plain(text="⛔ 你没有权限执行此操作。")]
                )
            )
            return

        if len(args) < 1:
            await event_context.reply(
                platform_message.MessageChain(
                    [platform_message.Plain(text="用法: !mute @用户 [时长]\n示例: !mute @张三 10m")]
                )
            )
            return

        target = args[0].strip("@").strip()
        duration_str = args[1] if len(args) > 1 else "10m"
        try:
            duration = self.plugin.parse_duration(duration_str)
        except (ValueError, IndexError):
            duration = 600

        try:
            await event_context.call_platform_api(
                "set_group_ban",
                group_id=event.launcher_id,
                user_id=target,
                duration=duration,
            )
            await event_context.reply(
                platform_message.MessageChain(
                    [platform_message.Plain(text=f"🔇 已禁言 {target}，时长 {duration_str}")]
                )
            )
        except Exception as e:
            await event_context.reply(
                platform_message.MessageChain(
                    [platform_message.Plain(text=f"❌ 禁言失败: {e}")]
                )
            )
