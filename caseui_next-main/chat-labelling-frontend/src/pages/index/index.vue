<template>
  <div>
    <Modal v-model="showInstructions" draggable scrollable title="操作说明">
      <div v-html="instructions_cus" v-if="role === 'cus'"></div>
      <div v-html="instructions_sys" v-if="role === 'sys'"></div>
      <div slot="footer">
        <Button type="primary" @click="showInstructions=false">关闭</Button>
      </div>
    </Modal>
    <profile v-show="needProfile" @completed="profileCompleted"/>
    <Card :bordered="false" dis-hover v-show="!finished&&!needProfile">
      <p slot="title" style="text-align:center;overflow:hidden">
        <strong slot="title">
          <Icon type="ios-chatbubbles-outline" :size="20" />
          当前用户是{{username}}，正在与用户{{partner}}聊天。
        </strong>
      </p>
      <div slot="extra">
        <Button type="text" @click="showInstructions=true">
          <Icon type="ios-information-circle-outline" />
          <span style="font-weight: bold; color: red;">操作说明</span>
        </Button>
      </div>
      <Spin size="large" v-if="loading" fix>
        <Icon type="ios-loading" size="50" class="spin-icon-load"></Icon>
        <div>{{message}}, please don't leave...</div>
      </Spin>
      <div>
        <Row :gutter="8">
          <Col :span="10">
            <chatUI ref="chatUI" :style="{height:(height+35)+'px',overflow:'auto'}" />
          </Col>
          <Col :span="14">
            <Alert type="warning" v-if="!finished">
              <strong>注意:</strong>
              <ul style="padding:0 10px;line-height:150%;font-size:80%">
                <li>
                  刷新页面可能会<strong>终止</strong>对话！
                </li>
                <li v-if="disabled">
                  请等待您聊天伙伴的消息。
                  <Button
                    style="margin-left:10px"
                    type="primary"
                    size="small"
                    @click="hurryup"
                    :disabled="hurryupLeftSeconds>0"
                  >催促您的对话对象{{hurryupLeftSeconds>0? ('('+hurryupLeftSeconds+'s)'):''}}</Button>
                </li>
              </ul>
            </Alert>
            <labelling
              :height="(height-20-(role=='cus'? 60:0))+'px'"
              ref="labelling"
              :role="role"
              :currentState="currentState"
              :searchData="searchData"
              :sendData="sendData"
              :sendDisabled="disabled"
              :actions="actions"
              :conversationId="conversationId"
              :finish="finish"
              :searchResultConfig="searchResultConfig"
              :searching="searching"
              :searchPanelLoading="searchPanelLoading"
              @on-filters="searchWithFilters"
              @states-backup="saveStatesBackup"
              @changeBackupForParent="saveChangeBackup"
              @getRecommendInfo="getRecommendInfo"
              :bus="bus"
            />
          </Col>
        </Row>
      </div>
    </Card>
    <rating v-show="finished&&!needProfile" :role="role" :userId="username" :conversationId="conversationId" :recommend_info="recommend_info" @completed="ratingCompleted"/>
  </div>
</template>
<script>
import chatUI from './chatUI'
import profile from './profile'
import labelling from './labelling'
import rating from './rating'
import util from '../../utils/util'
import Vue from 'vue'
import axios from 'axios'
import md5 from 'crypto-js/md5'
const maxHurryupLeftSeconds = 60
export default {
  components: {
    chatUI,
    labelling,
    rating,
    profile
  },
  mounted () {
    this.init()
    window.addEventListener('beforeunload', e => this.beforeunloadFn(e))
  },
  destroyed () {
    window.removeEventListener('beforeunload', e => this.beforeunloadFn(e))
    this.$socket.close()
  },
  data () {
    return {
      searching: false,
      searchPanelLoading: false,
      recommend_info: [],
      height: window.screen.availHeight - 230,
      loading: false,
      message: '',
      username: '',
      partner: '',
      conversationId: '',
      disabled: false,
      role: '',
      hurryupLeftSeconds: 0,
      actions: [],
      currentState: [],
      finished: false,
      needProfile: false,
      background: '',
      instructions: '',
      showInstructions: false,
      searchResultConfig: {},
      statesBackupList: [],
      bus: new Vue(),
      searchResultsBackup: {},
      selectedResultsBackup: [],
      instructions_cus: '感谢您同意参加此研究，您将扮演普通用户或系统角色进行对话。对话内容包括寻找一款产品（普通用户角色）或向用户推荐产品（系统角色）。附言：我们重视您的隐私。因此，我们将不会在此研究的任何手稿和其他公开材料上报告可识别的信息。<br><br>要完成此研究，请按照以下步骤操作。<br>1. 我们想了解您的一些一般信息，因此，在对话开始前，请您填写关于人口信息的调查问卷，其中的问题包括性别、年龄和专业等。<br>2. 接下来，您将与系统进行对话。对话将由您发起。您需要首先选择一个“意图”，然后在“回复”中编写一条消息以发送给系统（通过单击“发送”按钮）。在选择“意图”时，您可以将鼠标悬停在“？”图标旁边的“意图”上以查看每个“意图”的解释。如果您想要在一轮中发送多条消息，请确保在发送消息之前选中“发送另一条消息”。<br>3. 在您发送消息后，请等待系统回复或向您推荐产品。在收到系统消息后，您可以重复第2步以继续对话。<br>4. 当您认为对话已经完成时，您可以单击“结束对话”以结束对话。<br>5. 在单击“结束对话”后，您需要<strong>评价对话中系统推荐的产品的与您目标产品的相关性</strong>。因此，请确保您了解推荐产品与您的目标产品的相关性。',
      instructions_sys: '感谢您同意参加此研究，您将扮演普通用户或系统角色进行对话。对话内容包括寻找一款产品（普通用户角色）或向用户推荐产品（系统角色）。附言：我们重视您的隐私。因此，我们将不会在此研究的任何手稿和其他公开材料上报告可识别的信息。 <br><br>要完成此研究，请按照以下步骤操作。<br>1. 我们想了解您的一些一般信息，因此，在对话开始前，请您填写关于人口信息的调查问卷，其中的问题包括性别、年龄和专业等。<br>2. 接下来，您将与用户进行对话。请等待用户发送第一条消息。在您收到用户消息后，您需要首先选择一个“操作”。在选择“操作”时，您可以将鼠标悬停在“？”图标旁边的“操作”上以查看每个“操作”的解释。然后，在“回复”中编写一条消息（通过单击“发送”按钮）。如果您想要在一轮中发送多条消息，请确保在发送消息之前选中“发送另一条消息”。<br>3. 在每轮对话中，您可以在“查询”框内输入内容以搜索与产品相关的结果。在必要时，您还可以单击“显示过滤器选项”以查看筛选条件，并基于筛选条件搜索更相关的产品。请注意，搜索引擎可能会有些慢，请在提交查询后耐心等待结果。<br>4. 当您认为有产品满足用户的需求时，您可以在“操作”中选择“推荐”，并从搜索结果面板中选择相应的产品（通过选中产品的搜索结果旁边的复选框）以推荐给用户。在“回复”文本框中写下一条消息（例如：“以下选择如何？”），您选择的推荐产品将自动添加到您的文本消息中以发送给用户。<br>5. 当您认为需要了解更多关于用户需求的信息时，您可以在“操作”中选择“澄清”，并从结果面板中选择相应的“方向”（通过选中“方向”旁边的复选框），并在“回复”文本框中提出有关“方向”的澄清问题（例如，您更喜欢哪个操作系统？“操作系统”是您要提问的方向）。<br>6. 在用户完成对话并单击“结束对话”按钮后，您需要回答一些问卷调查以评价对话。'
    }
  },
  methods: {
    async getRecommendInfo () {
      try {
        // 调用后端API来获取搜索结果消息
        const response = await this.$http.get('/api/getSearchedMessage', {
          params: {
            conversationId: this.conversationId
          }
        })
        if (response.data !== null) {
          this.searchedMessage = response.data // 将搜索结果赋值给数据对象
          const regex = /href="[^"]*qid=(\d+&sr=\d+-\d+)/g // 提取qid和后续内容的正则表达式
          const matches = [...this.searchedMessage.matchAll(regex)] // 匹配所有链接中的qid和后续内容
          const productNames = this.searchedMessage ? this.searchedMessage.match(/>([^<]+)(?=<\/a>)/g).map(item => item.slice(1)) : [] // 提取产品名称
          // console.log(matches)
          console.log(productNames)
          if (productNames.length === 0) {
            this.recommend_info = []
            return
          }
          const recommendInfoMap = {} // 辅助对象用于去重
          this.recommend_info = matches.map((match, index) => {
            const name = productNames[index] // 获取产品名称
            // print(name)
            const id = md5(name).toString() // 提取qid
            if (!recommendInfoMap[name]) {
              recommendInfoMap[name] = true
              return { id, name }
            }
            return null // 已经添加过的id，返回null
          }).filter(item => item !== null)
        }
        // console.log(this.recommend_info)
      } catch (error) {
        console.error('Error fetching searched message:', error)
      }
    },
    beforeunloadFn (e) {
      if (this.finished) return
      // 这个事件只有在鼠标真正和浏览器有了交互，再刷新或者关闭时才会触发
      e = e || window.event
      if (e) {
        e.returnValue = '关闭提示'
      }
      return '关闭提示'
    },
    async init () {
      this.loadUser()
      this.loading = true
      this.message = 'Connecting to server'
      this.initWebSocket()
      // this.message = 'Checking profile'
      await this.checkProfile()
      // this.message = 'Loading instructions'
      await this.loadInstructions()
      // this.message = 'Loading search result config'
      await this.loadSearchResultConfig()
      // this.message = 'Loading actions'
      await this.loadAction()
      // this.message = 'Waiting for commands from server'
    },
    profileCompleted () {
      this.needProfile = false
    },
    ratingCompleted () {
      window.location = '/endchoice.html'
    },
    loadInstructions () {
      return this.$http.get('/api/instructions').then((response) => {
        this.instructions = response.data
      })
    },
    loadSearchResultConfig () {
      return this.$http.get('/api/loadSearchResultConfig').then((response) => {
        this.searchResultConfig = response.data
      })
    },
    checkProfile () {
      return this.$http.get('/api/checkProfile').then((response) => {
        this.needProfile = response.data
      })
    },
    initWebSocket () {
      let loc = window.location
      this.$connect('ws://' + loc.hostname + ':' + loc.port + '/websocket/' + this.username)
      this.$socket.onopen = this.websocketonopen
      this.$socket.onerror = this.websocketonerror
      this.$socket.onmessage = this.websocketonmessage
      this.$socket.onclose = this.websocketclose
    },
    finish (data, callback) {
      this.loading = true
      this.message = '对话结束！'
      this.websocketsend({type: 'FINISH'})
      callback()
    },
    reset () {
      this.loading = true
      this.message = ''
      this.partner = ''
      this.disabled = false
      this.role = ''
      this.finished = false
      this.$refs.chatUI.reset()
      this.$refs.labelling.reset()
    },
    websocketonopen (e) {
      // console.log('WebSocket连接成功', e)
    },

    websocketonerror (e) {
      // 错误
      this.$Notice.error(
        {
          title: '错误',
          desc: '服务器错误!'
        })
    },
    websocketonmessage (e) {
      const dataList = JSON.parse(e.data)
      dataList.map(async data => {
        // 数据接收，同步的执行方式，load数据完之后，才能往下执行
        if (data.messageCommand === 'START' && !this.finished) {
          this.$Notice.info(
            {
              title: '通知',
              desc: '您的对话对象已上线!'
            }
          )
          this.reset()
          let tempData = data.data
          this.partner = tempData.partner
          this.role = tempData.role
          this.conversationId = tempData.conversationId
          // this.userId = tempData.userId
          this.loading = true
          this.message = '正在读取'
          await this.loadHistoryAndBackground()
          this.loading = false
        }
        if (data.messageCommand === 'WAIT4PARTNER' && !this.finished) {
          this.message = '正在匹配'
          this.partner = ''
          this.role = ''
          this.loading = true
        }
        if (data.messageCommand === 'SENDMESSAGE' && !this.finished) {
          if (data.content) {
            this.$refs.chatUI.addMessage({message: data.content, time: new Date()}, 'sys')
          }
          if (this.role === 'sys') {
            this.loading = true
            this.disabled = true
            this.message = 'Loading states'
            await this.loadCurrentState()
          }
          this.loading = false
          this.disabled = false
        }
        if (data.messageCommand === 'WAIT4MESSAGE' && !this.finished) {
          if (data.content) {
            this.$refs.chatUI.addMessage({message: data.content, time: new Date()}, 'sys')
          }
          this.loading = false
          this.disabled = true
        }
        if (data.messageCommand === 'ERROR' && !this.finished) {
          if (data.conversationId >= 0) {
            this.$Notice.error(
              {
                title: '错误',
                desc: data.content
              }
            )
          } else {
            this.loading = true
            this.$Modal.warning({
              title: '提示',
              content: data.content
            })
          }
        }
        if (data.messageCommand === 'STOP' && !this.finished) {
          this.$Notice.error(
            {
              title: '错误',
              desc: '您的对话对象已经下线!'
            }
          )
          this.message = '正在等待您的对话对象重新连接'
          this.loading = true
        }
        if (data.messageCommand === 'HURRYUP' && !this.finished) {
          this.$Notice.warning(
            {
              title: '提示',
              desc: '请加快速度!'
            }
          )
        }
        if (data.messageCommand === 'FINISH') {
          this.finished = true
          this.$Notice.warning(
            {
              title: '提示',
              desc: '对话已结束，请在离开之前评价。'
            }
          )
          this.loading = false
          this.disabled = true
        }
      })
    },
    websocketsend (data) {
      this.$socket.send(JSON.stringify({
        from: this.username,
        to: this.partner,
        type: this.role === 'sys' ? 'SYS2CUS' : 'CUS2SYS',
        ...data
      }))
    },
    hurryup () {
      this.$socket.send(JSON.stringify({
        content: '请加快速度!',
        from: this.username,
        to: this.partner,
        type: 'HURRYUP'
      }))
      this.hurryupLeftSeconds = maxHurryupLeftSeconds
      let interval = setInterval(() => {
        this.hurryupLeftSeconds--
        if (this.hurryupLeftSeconds === 0) {
          clearInterval(interval)
        }
      }, 1000)
    },
    websocketclose (e) {
      // 关闭链接时触发
      var code = e.code//  状态码表 https://developer.mozilla.org/zh-CN/docs/Web/API/CloseEvent
      var reason = e.reason
      var wasClean = e.wasClean
      console.log(code, reason, wasClean)
    },
    loadUser () {
      this.username = util.parseUrl(location.href)._user
    },
    loadHistoryAndBackground () {
      const params = {
        sysName: this.role === 'sys' ? this.username : this.partner,
        cusName: this.role === 'cus' ? this.username : this.partner,
        conversationId: this.conversationId
      }
      return this.$http.get('/api/loadHistoryAndBackground', {params}).then((response) => {
        // todo 处理history
        if (response.data.history) {
          let history = []
          response.data.history.map(value => {
            history.unshift({
              message: value.content,
              time: value.updateTime,
              type: (value.type === 'CUS2SYS' && this.role === 'cus') || (value.type === 'SYS2CUS' && this.role === 'sys') ? 'user' : 'sys'
            })
          })
          this.$refs.chatUI.addHistoy(history)
        }
        if (response.data.background) {
          this.$refs.chatUI.addMessage({
            message: '<strong>您的角色: </strong>' + (this.role === 'sys' ? '系统. ' : '普通用户. ') + '<br/>' +
              (this.role === 'cus' ? '<strong>Background: </strong>' + response.data.background + '<br/>' : '') +
              '<strong>对话开始!</strong>' + '<br/>' + '注意: 由于需要在向您发送回应之前进行多个步骤，所以系统响应可能会有点慢，请耐心等待。',
            time: new Date()
          }, 'other')
          if (this.role === 'cus') {
            this.background = response.data.background
          } else {
            this.background = '请尝试帮助您的伙伴获取他/她的目标信息。'
          }
        }
      })
    },
    loadCurrentState () {
      return this.$http.get('/api/loadCurrentState').then((response) => {
        // this.currentState = response.data
        this.currentState = ''
      })
    },
    saveStatesBackup (newStates) {
      this.statesBackupList = newStates
      console.log('NEW STATES SAVED: ' + newStates)
    },
    searchWithFilters (newFilters) {
      console.log('Searching with filters: ' + newFilters)
      console.log('Searching for the query:  ' + this.statesBackupList)
      if (this.statesBackupList.length === 0 || newFilters.length === 0) {
        return
      }
      // debugger
      let that = this
      let url = 'http://localhost:9191?query=' + encodeURIComponent(this.statesBackupList.join(' ')) + '&refinements=' + encodeURIComponent(newFilters.join(','))
      axios.get(
        url, { timeout: 30000 }
      ).then((json) => {
        if (json.data.ref === 'error') {
          this.$Notice.warning({
            title: '警告',
            desc: '您选择了太多限制，请重新选择。'
          })
          return
        }
        // debugger
        this.$http.post('/api/saveSearchResults', {
          query: this.statesBackupList.join(' '),
          filter: newFilters.join(' '),
          conversationId: this.conversationId,
          data: json.data
        })
        this.$Notice.success({
          title: '成功!',
          desc: '搜索成功.'
        })
        this.searchResultsBackup = json.data
        that.bus.$emit('loadMore', json.data)
      }).catch((error) => {
        console.log(error)
        this.$Notice.error({
          title: '错误',
          desc: '请刷新页面或更改查询以重新搜索!'
        })
        let emptyData = {
          Answer: [],
          Suggest: [],
          Filters: [],
          Aspects: []
        }
        this.searchResultsBackup = emptyData
        that.bus.$emit('loadMore', emptyData)
      })
    },
    searchData (states, callback) {
      if (states.length === 0) {
        return
      }
      console.log('Searching for ' + states)
      this.$Notice.info({
        title: '搜索中',
        desc: '搜索中，请稍候'
      })
      this.searching = true
      this.searchPanelLoading = false
      let url = 'http://localhost:9191?query=' + encodeURIComponent(states.join(' '))
      axios.get(
        url, { timeout: 30000 }
      ).then((json) => {
        if (json.data.key === 'error') {
          this.$Notice.warning({
            title: '警告',
            desc: '查询范围过大，请选择一个更精确的查询。'
          })
          let emptyData = {
            Answer: [],
            Suggest: [],
            Filters: [],
            Aspects: []
          }
          this.searchResultsBackup = emptyData
          callback(emptyData)
          return
        }
        this.$http.post('/api/saveSearchResults', {
          query: states.join(' '),
          filter: '',
          conversationId: this.conversationId,
          data: json.data
        })
        console.log('Search successful.')
        this.$Notice.success({
          title: '成功!',
          desc: '搜索成功.'
        })
        this.searchResultsBackup = json.data
        callback(json.data)
      }).catch((error) => {
        console.log(error)
        this.$Notice.error({
          title: '错误',
          desc: '请刷新页面或更改查询以重新搜索!'
        })
        let emptyData = {
          Answer: [],
          Suggest: [],
          Filters: [],
          Aspects: []
        }
        this.searchResultsBackup = emptyData
        callback(emptyData)
      })
    },
    loadAction () {
      return this.$http.get('/api/loadActions').then((response) => {
        this.actions = response.data
      })
    },
    sendData (data, callback) {
      console.log(data.sendAnother)
      this.loading = true
      this.message = 'Sending message'
      let msg = data.response
      console.log('response')
      console.log(data.response)
      console.log(this.selectedResultsBackup)
      for (let i = 0; i < this.selectedResultsBackup.length; i++) {
        let item = this.selectedResultsBackup[i]
        if (item.hasOwnProperty('link')) {
          msg += `<div style="display: flex; align-items: center;"><img src="${item.image}" alt="${item.title}" height="50px" width="50px" style="margin-right: 10px;"> <a style="color: yellowgreen" target="_blank" href="${item.link}">${item.title}</a></div>`
        }
        if (i < this.selectedResultsBackup.length - 1) {
          msg += '<br>' // Add an empty line between results
        }
      }
      data.response = msg
      console.log('data:')
      console.log(data)
      this.websocketsend(data)
      this.$refs.chatUI.addMessage({message: msg, time: new Date()}, 'user')
      callback()
    },
    saveChangeBackup (checked) {
      this.selectedResultsBackup = checked
    }
  }
}
</script>
