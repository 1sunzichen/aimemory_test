package main

import (
	"bufio"
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"math"
	"net/http"
	"os"
	"strconv"
	"strings"
	"time"
	"unicode"
)

// ====== API 结构体 ======

type Message struct {
	Role       string     `json:"role"`
	Content    string     `json:"content,omitempty"`
	ToolCalls  []ToolCall `json:"tool_calls,omitempty"`
	ToolCallID string     `json:"tool_call_id,omitempty"`
}

type ToolCall struct {
	ID       string           `json:"id"`
	Type     string           `json:"type"`
	Function ToolCallFunction `json:"function"`
}

type ToolCallFunction struct {
	Name      string `json:"name"`
	Arguments string `json:"arguments"`
}

type Tool struct {
	Type     string       `json:"type"`
	Function ToolFunction `json:"function"`
}

type ToolFunction struct {
	Name        string         `json:"name"`
	Description string         `json:"description"`
	Parameters  ToolParameters `json:"parameters"`
}

type ToolParameters struct {
	Type       string              `json:"type"`
	Properties map[string]Property `json:"properties"`
	Required   []string            `json:"required,omitempty"`
}

type Property struct {
	Type        string `json:"type"`
	Description string `json:"description"`
}

type ChatRequest struct {
	Model    string    `json:"model"`
	Messages []Message `json:"messages"`
	Tools    []Tool    `json:"tools,omitempty"`
}

type ChatResponse struct {
	Choices []struct {
		Message Message `json:"message"`
	} `json:"choices"`
}

// ====== 工具函数 ======

func getWeather(args map[string]any) string {
	city, _ := args["city"].(string)
	data := map[string]string{
		"北京": "晴，25°C，北风3级",
		"上海": "多云，28°C，东南风2级",
		"东京": "小雨，22°C，西风4级",
		"纽约": "阴，18°C，北风5级",
		"广州": "晴，32°C，微风",
		"深圳": "多云，30°C，南风2级",
	}
	if v, ok := data[city]; ok {
		return v
	}
	return city + "：晴天，20°C（模拟数据）"
}

func calculator(args map[string]any) string {
	expr, _ := args["expression"].(string)
	for _, c := range expr {
		if !unicode.IsDigit(c) && !strings.ContainsRune("+-*/.() ", c) {
			return "错误：表达式包含不允许的字符"
		}
	}
	result, err := evalExpr(expr)
	if err != nil {
		return "计算出错：" + err.Error()
	}
	return fmt.Sprintf("%s = %g", expr, result)
}

func currentTime(args map[string]any) string {
	now := time.Now()
	return fmt.Sprintf("现在是 %d年%d月%d日 %02d:%02d",
		now.Year(), now.Month(), now.Day(), now.Hour(), now.Minute())
}

func searchWeb(args map[string]any) string {
	query, _ := args["query"].(string)
	data := map[string]string{
		"python":  "Python 是目前最流行的编程语言之一，广泛用于 AI、数据分析、Web 开发。",
		"deepseek": "DeepSeek 是中国深度求索公司开发的 AI 大模型，性价比极高，开源免费。",
		"水浒传":  "《水浒传》是元末明初施耐庵所著，讲 108 位好汉被逼上梁山的故事。",
		"openai":  "OpenAI 是 GPT 系列模型的开发公司，旗下有 ChatGPT 等产品。",
		"人工智能": "人工智能（AI）是让计算机模拟人类智能的技术，当前以大语言模型为代表。",
	}
	lower := strings.ToLower(query)
	for k, v := range data {
		if strings.Contains(lower, k) {
			return v
		}
	}
	return fmt.Sprintf("关于「%s」没有找到相关信息（模拟搜索）。", query)
}

func setReminder(args map[string]any) string {
	content, _ := args["content"].(string)
	minutes := 0
	switch v := args["minutes"].(type) {
	case float64:
		minutes = int(v)
	case string:
		minutes, _ = strconv.Atoi(v)
	}
	return fmt.Sprintf("已设置提醒：%d 分钟后提醒你「%s」（模拟，实际不会弹出通知）", minutes, content)
}

// ====== 工具清单 ======

var tools = []Tool{
	{Type: "function", Function: ToolFunction{
		Name: "get_weather", Description: "查询指定城市的天气",
		Parameters: ToolParameters{
			Type:       "object",
			Properties: map[string]Property{"city": {Type: "string", Description: "城市名称，如 北京、上海"}},
			Required:   []string{"city"},
		},
	}},
	{Type: "function", Function: ToolFunction{
		Name: "calculator", Description: "计算数学表达式，支持加减乘除和括号",
		Parameters: ToolParameters{
			Type:       "object",
			Properties: map[string]Property{"expression": {Type: "string", Description: "数学表达式，如 '(3+5)*2'"}},
			Required:   []string{"expression"},
		},
	}},
	{Type: "function", Function: ToolFunction{
		Name:       "current_time",
		Description: "获取当前日期和时间",
		Parameters: ToolParameters{Type: "object", Properties: map[string]Property{}},
	}},
	{Type: "function", Function: ToolFunction{
		Name: "search_web", Description: "搜索网页获取信息",
		Parameters: ToolParameters{
			Type:       "object",
			Properties: map[string]Property{"query": {Type: "string", Description: "搜索关键词"}},
			Required:   []string{"query"},
		},
	}},
	{Type: "function", Function: ToolFunction{
		Name: "set_reminder", Description: "设置一个定时提醒",
		Parameters: ToolParameters{
			Type: "object",
			Properties: map[string]Property{
				"content": {Type: "string", Description: "提醒内容"},
				"minutes": {Type: "integer", Description: "多少分钟后提醒"},
			},
			Required: []string{"content", "minutes"},
		},
	}},
}

var functions = map[string]func(map[string]any) string{
	"get_weather":  getWeather,
	"calculator":   calculator,
	"current_time": currentTime,
	"search_web":   searchWeb,
	"set_reminder": setReminder,
}

// ====== API 调用 ======

func callAPI(messages []Message, withTools bool) (*Message, error) {
	req := ChatRequest{Model: "deepseek-chat", Messages: messages}
	if withTools {
		req.Tools = tools
	}

	body, _ := json.Marshal(req)
	httpReq, _ := http.NewRequest("POST", "https://api.deepseek.com/v1/chat/completions", bytes.NewReader(body))
	httpReq.Header.Set("Content-Type", "application/json")
	httpReq.Header.Set("Authorization", "Bearer "+os.Getenv("DEEPSEEK_API_KEY"))

	resp, err := http.DefaultClient.Do(httpReq)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	data, _ := io.ReadAll(resp.Body)
	var result ChatResponse
	if err := json.Unmarshal(data, &result); err != nil {
		return nil, err
	}
	if len(result.Choices) == 0 {
		return nil, fmt.Errorf("空响应：%s", string(data))
	}
	msg := result.Choices[0].Message
	return &msg, nil
}

// ====== 处理一轮对话 ======

func chatOnce(messages *[]Message) (string, error) {
	msg, err := callAPI(*messages, true)
	if err != nil {
		return "", err
	}

	if len(msg.ToolCalls) == 0 {
		*messages = append(*messages, *msg)
		return msg.Content, nil
	}

	*messages = append(*messages, *msg)

	for _, tc := range msg.ToolCalls {
		var args map[string]any
		json.Unmarshal([]byte(tc.Function.Arguments), &args)

		fmt.Printf("  [工具] %s(%v)\n", tc.Function.Name, args)

		fn, ok := functions[tc.Function.Name]
		result := "未知工具"
		if ok {
			result = fn(args)
		}
		fmt.Printf("  [结果] %s\n", result)

		*messages = append(*messages, Message{
			Role:       "tool",
			Content:    result,
			ToolCallID: tc.ID,
		})
	}

	final, err := callAPI(*messages, false)
	if err != nil {
		return "", err
	}
	*messages = append(*messages, *final)
	return final.Content, nil
}

// ====== 加载 .env 文件 ======

func loadEnv() {
	data, err := os.ReadFile(".env")
	if err != nil {
		return
	}
	for _, line := range strings.Split(string(data), "\n") {
		line = strings.TrimSpace(line)
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}
		parts := strings.SplitN(line, "=", 2)
		if len(parts) != 2 {
			continue
		}
		key := strings.TrimSpace(parts[0])
		val := strings.Trim(strings.TrimSpace(parts[1]), `"'`)
		os.Setenv(key, val)
	}
}

// ====== 主程序 ======

func main() {
	loadEnv()

	apiKey := os.Getenv("DEEPSEEK_API_KEY")
	if apiKey == "" {
		fmt.Println("错误：未设置 DEEPSEEK_API_KEY 环境变量")
		os.Exit(1)
	}

	messages := []Message{
		{
			Role: "system",
			Content: "你是一个全能命令行助手，名字叫支离奇。" +
				"你拥有以下工具：查天气、数学计算、查看时间、搜索网页、设置提醒。" +
				"遇到需要查询或计算的问题时，主动调用工具而不是猜测。回答简洁，用中文。",
		},
	}

	fmt.Println(strings.Repeat("=", 45))
	fmt.Println("   支离奇  |  聊天 + 工具调用  (Go版)")
	fmt.Println(strings.Repeat("=", 45))
	fmt.Println("可以问我：天气 / 计算 / 时间 / 搜索 / 提醒")
	fmt.Println("输入 history 查看对话记录，quit 退出\n")

	scanner := bufio.NewScanner(os.Stdin)
	for {
		fmt.Print("你: ")
		if !scanner.Scan() {
			fmt.Println("\n👋 再见！")
			break
		}
		user := strings.TrimSpace(scanner.Text())
		if user == "" {
			continue
		}
		if user == "quit" {
			fmt.Println("👋 再见！")
			break
		}
		if user == "history" {
			fmt.Println("\n--- 对话记录 ---")
			for _, m := range messages[1:] {
				role := map[string]string{"user": "你", "assistant": "AI", "tool": "工具"}[m.Role]
				if m.Content != "" {
					content := m.Content
					if len([]rune(content)) > 80 {
						content = string([]rune(content)[:80]) + "..."
					}
					fmt.Printf("%s: %s\n", role, content)
				}
			}
			fmt.Println("----------------\n")
			continue
		}

		messages = append(messages, Message{Role: "user", Content: user})

		reply, err := chatOnce(&messages)
		if err != nil {
			fmt.Println("错误：", err)
			continue
		}
		fmt.Printf("支离奇: %s\n\n", reply)
	}
}

// ====== 简易数学表达式求值 ======

func evalExpr(expr string) (float64, error) {
	expr = strings.ReplaceAll(expr, " ", "")
	val, _, err := parseExpr(expr, 0)
	return val, err
}

func parseExpr(expr string, pos int) (float64, int, error) {
	return parseAddSub(expr, pos)
}

func parseAddSub(expr string, pos int) (float64, int, error) {
	left, pos, err := parseMulDiv(expr, pos)
	if err != nil {
		return 0, pos, err
	}
	for pos < len(expr) && (expr[pos] == '+' || expr[pos] == '-') {
		op := expr[pos]
		pos++
		right, newPos, err := parseMulDiv(expr, pos)
		if err != nil {
			return 0, newPos, err
		}
		pos = newPos
		if op == '+' {
			left += right
		} else {
			left -= right
		}
	}
	return left, pos, nil
}

func parseMulDiv(expr string, pos int) (float64, int, error) {
	left, pos, err := parseUnary(expr, pos)
	if err != nil {
		return 0, pos, err
	}
	for pos < len(expr) && (expr[pos] == '*' || expr[pos] == '/') {
		op := expr[pos]
		pos++
		right, newPos, err := parseUnary(expr, pos)
		if err != nil {
			return 0, newPos, err
		}
		pos = newPos
		if op == '*' {
			left *= right
		} else {
			if right == 0 {
				return 0, pos, fmt.Errorf("除以零")
			}
			left /= right
		}
	}
	return left, pos, nil
}

func parseUnary(expr string, pos int) (float64, int, error) {
	if pos < len(expr) && expr[pos] == '-' {
		val, pos, err := parsePrimary(expr, pos+1)
		return -val, pos, err
	}
	return parsePrimary(expr, pos)
}

func parsePrimary(expr string, pos int) (float64, int, error) {
	if pos < len(expr) && expr[pos] == '(' {
		val, pos, err := parseAddSub(expr, pos+1)
		if err != nil {
			return 0, pos, err
		}
		if pos >= len(expr) || expr[pos] != ')' {
			return 0, pos, fmt.Errorf("缺少右括号")
		}
		return val, pos + 1, nil
	}
	start := pos
	for pos < len(expr) && (unicode.IsDigit(rune(expr[pos])) || expr[pos] == '.') {
		pos++
	}
	if start == pos {
		return 0, pos, fmt.Errorf("无效表达式")
	}
	val, err := strconv.ParseFloat(expr[start:pos], 64)
	_ = math.Pi // 保持 math 包引用
	return val, pos, err
}
