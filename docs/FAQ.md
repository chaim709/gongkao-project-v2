# 常见问题 FAQ

## 使用问题

### Q: 登录不了怎么办？
**A**:
1. 确认用户名和密码是否正确（初始密码见操作手册）
2. 检查后端服务是否正常运行：访问 http://localhost:8000/health
3. 检查浏览器控制台是否有网络错误

### Q: 页面空白或加载不出来？
**A**:
1. 清除浏览器缓存（Ctrl+Shift+Delete）
2. 检查前端服务是否启动
3. 尝试使用无痕模式打开

### Q: 删除的数据能恢复吗？
**A**: 可以。系统使用软删除机制，数据不会真正从数据库中移除。需要联系管理员通过数据库操作恢复。

### Q: 手机号提示格式错误？
**A**: 手机号必须是 11 位数字，以 1 开头（如 13812345678）。

### Q: 如何修改密码？
**A**: 当前版本暂不支持前端修改密码，需要管理员通过后台修改。

---

## 运维问题

### Q: 如何查看服务日志？
```bash
# 查看所有日志
./deploy.sh logs

# 只看后端日志
./deploy.sh logs backend

# 只看数据库日志
./deploy.sh logs db
```

### Q: 如何备份数据库？
```bash
./deploy.sh backup
# 备份文件保存在 backups/ 目录下
```

### Q: 如何恢复数据库？
```bash
# 解压备份文件
gunzip backups/gongkao_db_20260306.sql.gz

# 恢复
docker compose -f docker-compose.prod.yml exec -T db \
  psql -U gongkao_user gongkao_db < backups/gongkao_db_20260306.sql
```

### Q: 服务异常如何重启？
```bash
./deploy.sh restart
```

### Q: 如何更新代码？
```bash
# 拉取最新代码
git pull

# 更新部署（自动备份 + 重建）
./deploy.sh update
```

### Q: 磁盘空间不足？
1. 清理旧的 Docker 镜像：`docker system prune -a`
2. 清理旧备份：旧备份会自动清理（保留30��）
3. 清理上传文件中的过期文件

---

## 开发问题

### Q: 本地开发环境怎么搭建？
参见 [SETUP.md](../SETUP.md)

### Q: 如何新增 API？
1. 在 `backend/app/models/` 创建模型
2. 在 `backend/app/schemas/` 创建 Schema
3. 在 `backend/app/repositories/` 创建数据访问层
4. 在 `backend/app/services/` 创建业务逻辑层
5. 在 `backend/app/routes/` 创建路由
6. 在 `backend/app/main.py` 注册路由
7. 创建数据库迁移：`alembic revision --autogenerate -m "描述"`
8. 执行迁移：`alembic upgrade head`

### Q: 如何新增前端页面？
1. 在 `frontend/src/pages/` 创建页面组件
2. 在 `frontend/src/api/` 创建 API 调用
3. 在 `frontend/src/App.tsx` 添加路由
4. 在 `frontend/src/components/layout/MainLayout.tsx` 添加菜单项
