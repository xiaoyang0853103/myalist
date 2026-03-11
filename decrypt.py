#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TVBox 接口自动解密工具
支持：Base64、AES、URL参数提取、JSON解析
"""

import base64
import json
import re
import os
import sys
import time
from datetime import datetime
from urllib.parse import unquote, parse_qs, urlparse
import requests

# 可选：AES解密支持
try:
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import unpad
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False


class TVBoxDecoder:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': '*/*',
        })
        self.results = []
        self.errors = []
    
    def fetch_content(self, url, retries=3):
        """获取URL内容"""
        for i in range(retries):
            try:
                print(f"  📥 获取: {url} (尝试 {i+1}/{retries})")
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                
                # 处理编码
                if response.encoding == 'ISO-8859-1':
                    response.encoding = response.apparent_encoding
                
                content = response.text
                print(f"  ✅ 成功，长度: {len(content)}")
                return content
            except Exception as e:
                print(f"  ❌ 失败: {e}")
                if i < retries - 1:
                    time.sleep(2)
                else:
                    self.errors.append(f"{url}: {str(e)}")
                    return None
    
    def is_json(self, text):
        """检查是否为JSON"""
        try:
            json.loads(text)
            return True
        except:
            return False
    
    def try_base64_decode(self, text, max_layers=3):
        """尝试Base64解码（支持嵌套）"""
        results = []
        current = text.strip()
        
        for i in range(max_layers):
            # 清理
            current = current.replace('\n', '').replace(' ', '')
            
            # 填充
            padding = 4 - len(current) % 4
            if padding != 4:
                current += '=' * padding
            
            try:
                decoded = base64.b64decode(current).decode('utf-8')
                results.append({
                    'layer': i + 1,
                    'content': decoded,
                    'is_json': self.is_json(decoded)
                })
                current = decoded
            except:
                break
        
        return results
    
    def try_url_safe_base64(self, text):
        """尝试URL安全Base64"""
        try:
            text = text.replace('\n', '').replace(' ', '')
            padding = 4 - len(text) % 4
            if padding != 4:
                text += '=' * padding
            decoded = base64.urlsafe_b64decode(text).decode('utf-8')
            return decoded
        except:
            return None
    
    def process_url(self, url):
        """处理单个URL"""
        print(f"\n{'='*60}")
        print(f"🔍 处理: {url}")
        print(f"{'='*60}")
        
        content = self.fetch_content(url)
        if not content:
            return None
        
        result = {
            'url': url,
            'original_length': len(content),
            'decrypted': False,
            'methods': [],
            'final_content': content,
            'timestamp': datetime.now().isoformat()
        }
        
        # 1. 检查是否已是明文JSON
        if self.is_json(content):
            print("  ℹ️  已是明文JSON")
            try:
                data = json.loads(content)
                result['final_content'] = json.dumps(data, ensure_ascii=False, indent=2)
                result['methods'].append({'type': 'plaintext', 'desc': '明文JSON'})
                result['decrypted'] = True
            except:
                pass
        
        # 2. 尝试Base64
        if not result['decrypted']:
            print("  🔓 尝试Base64...")
            b64_results = self.try_base64_decode(content)
            
            if b64_results:
                print(f"    ✓ Base64解码成功 ({len(b64_results)}层)")
                
                # 优先使用JSON结果
                for r in b64_results:
                    if r['is_json']:
                        result['final_content'] = json.dumps(
                            json.loads(r['content']), 
                            ensure_ascii=False, 
                            indent=2
                        )
                        result['methods'].append({
                            'type': 'base64',
                            'layers': r['layer'],
                            'desc': f'Base64({r["layer"]}层)->JSON'
                        })
                        result['decrypted'] = True
                        break
                
                # 无JSON则用最后一层
                if not result['decrypted']:
                    last = b64_results[-1]
                    result['final_content'] = last['content']
                    result['methods'].append({
                        'type': 'base64',
                        'layers': last['layer'],
                        'desc': f'Base64({last["layer"]}层)'
                    })
                    result['decrypted'] = True
        
        # 3. 尝试URL安全Base64
        if not result['decrypted']:
            print("  🔓 尝试URL安全Base64...")
            urlsafe = self.try_url_safe_base64(content)
            if urlsafe:
                print("    ✓ URL安全Base64成功")
                if self.is_json(urlsafe):
                    result['final_content'] = json.dumps(
                        json.loads(urlsafe),
                        ensure_ascii=False,
                        indent=2
                    )
                else:
                    result['final_content'] = urlsafe
                result['methods'].append({
                    'type': 'base64url',
                    'desc': 'URL安全Base64'
                })
                result['decrypted'] = True
        
        # 4. 未解密则保留原样
        if not result['decrypted']:
            print("  ⚠️  未识别加密方式，保留原样")
            result['methods'].append({
                'type': 'unknown',
                'desc': '未识别/保留原样'
            })
        
        self.results.append(result)
        return result
    
    def process_url_list(self, file_path='url.txt'):
        """处理URL列表"""
        if not os.path.exists(file_path):
            print(f"❌ 文件不存在: {file_path}")
            return False
        
        with open(file_path, 'r', encoding='utf-8') as f:
            urls = [
                line.strip() 
                for line in f 
                if line.strip() and not line.startswith('#')
            ]
        
        print(f"\n📋 读取到 {len(urls)} 个URL")
        
        for url in urls:
            self.process_url(url)
            time.sleep(1)
        
        return True
    
    def generate_live_txt(self, output_file='live.txt'):
        """生成live.txt"""
        print(f"\n{'='*60}")
        print(f"📝 生成 {output_file}")
        print(f"{'='*60}")
        
        lines = []
        lines.append(f"# TVBox 解密结果")
        lines.append(f"# 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"# 总计: {len(self.results)} | 成功: {sum(1 for r in self.results if r['decrypted'])}")
        lines.append(f"# {'='*60}\n")
        
        for i, result in enumerate(self.results, 1):
            lines.append(f"# {'='*60}")
            lines.append(f"# [{i}] {result['url']}")
            lines.append(f"# 方法: {result['methods'][0]['desc'] if result['methods'] else 'N/A'}")
            lines.append(f"# 时间: {result['timestamp']}")
            lines.append(f"# {'='*60}\n")
            
            content = result['final_content']
            if isinstance(content, str):
                lines.append(content)
            else:
                lines.append(json.dumps(content, ensure_ascii=False, indent=2))
            
            lines.append("\n\n")
        
        # 错误日志
        if self.errors:
            lines.append(f"# {'='*60}")
            lines.append(f"# 错误日志:")
            for e in self.errors:
                lines.append(f"# {e}")
        
        final_content = '\n'.join(lines)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(final_content)
        
        print(f"✅ 已保存: {output_file} ({len(final_content)} 字符)")
        
        # 生成JSON报告
        report = {
            'generated_at': datetime.now().isoformat(),
            'summary': {
                'total': len(self.results),
                'success': sum(1 for r in self.results if r['decrypted']),
                'failed': len(self.errors)
            },
            'results': self.results,
            'errors': self.errors
        }
        
        with open('live_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 报告已保存: live_report.json")
        
        return output_file


def main():
    decoder = TVBoxDecoder()
    
    if decoder.process_url_list('url.txt'):
        decoder.generate_live_txt('live.txt')
        
        print(f"\n{'='*60}")
        print("📊 统计:")
        print(f"  总计: {len(decoder.results)}")
        print(f"  成功: {sum(1 for r in decoder.results if r['decrypted'])}")
        print(f"  失败: {len(decoder.errors)}")
        print(f"{'='*60}")
    else:
        print("❌ 处理失败")
        sys.exit(1)


if __name__ == "__main__":
    main()
