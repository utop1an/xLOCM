;; blocks=250, out_folder=testing/hard, instance_id=9, seed=1015

(define (problem blocksworld-09)
 (:domain blocksworld)
 (:objects b1 b2 b3 b4 b5 b6 b7 b8 b9 b10 b11 b12 b13 b14 b15 b16 b17 b18 b19 b20 b21 b22 b23 b24 b25 b26 b27 b28 b29 b30 b31 b32 b33 b34 b35 b36 b37 b38 b39 b40 b41 b42 b43 b44 b45 b46 b47 b48 b49 b50 b51 b52 b53 b54 b55 b56 b57 b58 b59 b60 b61 b62 b63 b64 b65 b66 b67 b68 b69 b70 b71 b72 b73 b74 b75 b76 b77 b78 b79 b80 b81 b82 b83 b84 b85 b86 b87 b88 b89 b90 b91 b92 b93 b94 b95 b96 b97 b98 b99 b100 b101 b102 b103 b104 b105 b106 b107 b108 b109 b110 b111 b112 b113 b114 b115 b116 b117 b118 b119 b120 b121 b122 b123 b124 b125 b126 b127 b128 b129 b130 b131 b132 b133 b134 b135 b136 b137 b138 b139 b140 b141 b142 b143 b144 b145 b146 b147 b148 b149 b150 b151 b152 b153 b154 b155 b156 b157 b158 b159 b160 b161 b162 b163 b164 b165 b166 b167 b168 b169 b170 b171 b172 b173 b174 b175 b176 b177 b178 b179 b180 b181 b182 b183 b184 b185 b186 b187 b188 b189 b190 b191 b192 b193 b194 b195 b196 b197 b198 b199 b200 b201 b202 b203 b204 b205 b206 b207 b208 b209 b210 b211 b212 b213 b214 b215 b216 b217 b218 b219 b220 b221 b222 b223 b224 b225 b226 b227 b228 b229 b230 b231 b232 b233 b234 b235 b236 b237 b238 b239 b240 b241 b242 b243 b244 b245 b246 b247 b248 b249 b250 - object)
 (:init 
    (arm-empty)
    (clear b247)
    (on-table b247)
    (clear b180)
    (on b180 b234)
    (on b234 b19)
    (on b19 b95)
    (on b95 b36)
    (on b36 b211)
    (on-table b211)
    (clear b13)
    (on-table b13)
    (clear b231)
    (on b231 b137)
    (on b137 b216)
    (on b216 b249)
    (on b249 b154)
    (on b154 b68)
    (on b68 b193)
    (on b193 b90)
    (on b90 b233)
    (on b233 b26)
    (on b26 b25)
    (on-table b25)
    (clear b241)
    (on b241 b131)
    (on b131 b104)
    (on b104 b189)
    (on b189 b183)
    (on b183 b145)
    (on-table b145)
    (clear b111)
    (on-table b111)
    (clear b132)
    (on b132 b52)
    (on b52 b54)
    (on b54 b168)
    (on-table b168)
    (clear b179)
    (on b179 b143)
    (on b143 b51)
    (on b51 b55)
    (on b55 b6)
    (on b6 b140)
    (on b140 b91)
    (on b91 b61)
    (on b61 b117)
    (on b117 b23)
    (on b23 b83)
    (on-table b83)
    (clear b115)
    (on b115 b41)
    (on-table b41)
    (clear b80)
    (on b80 b97)
    (on b97 b226)
    (on b226 b232)
    (on b232 b105)
    (on b105 b198)
    (on b198 b32)
    (on b32 b224)
    (on b224 b187)
    (on b187 b182)
    (on b182 b74)
    (on b74 b219)
    (on-table b219)
    (clear b215)
    (on b215 b156)
    (on-table b156)
    (clear b178)
    (on b178 b141)
    (on b141 b246)
    (on-table b246)
    (clear b87)
    (on b87 b130)
    (on b130 b39)
    (on b39 b22)
    (on b22 b102)
    (on b102 b128)
    (on b128 b93)
    (on b93 b56)
    (on-table b56)
    (clear b134)
    (on b134 b242)
    (on b242 b162)
    (on b162 b172)
    (on b172 b245)
    (on b245 b204)
    (on b204 b197)
    (on b197 b15)
    (on b15 b81)
    (on b81 b250)
    (on b250 b94)
    (on b94 b50)
    (on b50 b148)
    (on b148 b228)
    (on b228 b31)
    (on b31 b124)
    (on b124 b235)
    (on b235 b165)
    (on b165 b108)
    (on b108 b229)
    (on b229 b42)
    (on b42 b116)
    (on b116 b138)
    (on b138 b48)
    (on b48 b24)
    (on b24 b71)
    (on b71 b203)
    (on b203 b100)
    (on b100 b185)
    (on b185 b118)
    (on b118 b167)
    (on b167 b169)
    (on b169 b120)
    (on-table b120)
    (clear b119)
    (on b119 b16)
    (on b16 b223)
    (on b223 b218)
    (on b218 b67)
    (on b67 b62)
    (on b62 b35)
    (on b35 b89)
    (on b89 b210)
    (on b210 b153)
    (on b153 b82)
    (on b82 b45)
    (on b45 b177)
    (on b177 b10)
    (on b10 b158)
    (on-table b158)
    (clear b20)
    (on b20 b77)
    (on b77 b4)
    (on b4 b63)
    (on b63 b96)
    (on b96 b92)
    (on b92 b69)
    (on b69 b75)
    (on b75 b38)
    (on b38 b40)
    (on b40 b76)
    (on b76 b7)
    (on b7 b164)
    (on b164 b238)
    (on b238 b5)
    (on b5 b126)
    (on b126 b113)
    (on b113 b84)
    (on b84 b43)
    (on b43 b209)
    (on b209 b49)
    (on b49 b171)
    (on b171 b86)
    (on b86 b181)
    (on-table b181)
    (clear b65)
    (on-table b65)
    (clear b70)
    (on b70 b199)
    (on b199 b46)
    (on b46 b174)
    (on b174 b44)
    (on b44 b11)
    (on b11 b149)
    (on b149 b110)
    (on b110 b186)
    (on b186 b37)
    (on b37 b163)
    (on b163 b217)
    (on-table b217)
    (clear b8)
    (on b8 b14)
    (on b14 b208)
    (on b208 b237)
    (on b237 b139)
    (on b139 b176)
    (on b176 b159)
    (on-table b159)
    (clear b133)
    (on b133 b201)
    (on-table b201)
    (clear b144)
    (on b144 b33)
    (on b33 b194)
    (on b194 b155)
    (on b155 b147)
    (on b147 b99)
    (on b99 b122)
    (on b122 b221)
    (on b221 b214)
    (on b214 b175)
    (on b175 b17)
    (on b17 b190)
    (on b190 b121)
    (on-table b121)
    (clear b9)
    (on b9 b64)
    (on b64 b58)
    (on b58 b57)
    (on b57 b21)
    (on b21 b227)
    (on-table b227)
    (clear b239)
    (on b239 b101)
    (on b101 b2)
    (on b2 b136)
    (on b136 b244)
    (on b244 b47)
    (on-table b47)
    (clear b1)
    (on b1 b28)
    (on b28 b34)
    (on-table b34)
    (clear b107)
    (on-table b107)
    (clear b53)
    (on b53 b146)
    (on b146 b88)
    (on b88 b202)
    (on b202 b150)
    (on b150 b142)
    (on b142 b114)
    (on b114 b205)
    (on b205 b73)
    (on-table b73)
    (clear b109)
    (on b109 b66)
    (on b66 b18)
    (on b18 b30)
    (on b30 b152)
    (on b152 b98)
    (on b98 b157)
    (on b157 b59)
    (on b59 b12)
    (on b12 b248)
    (on b248 b213)
    (on b213 b243)
    (on b243 b60)
    (on b60 b192)
    (on b192 b166)
    (on b166 b161)
    (on b161 b85)
    (on b85 b129)
    (on b129 b222)
    (on b222 b127)
    (on b127 b206)
    (on b206 b106)
    (on b106 b220)
    (on b220 b29)
    (on-table b29)
    (clear b191)
    (on b191 b236)
    (on b236 b3)
    (on b3 b200)
    (on b200 b160)
    (on b160 b230)
    (on b230 b188)
    (on-table b188)
    (clear b123)
    (on b123 b79)
    (on b79 b212)
    (on b212 b170)
    (on b170 b151)
    (on b151 b112)
    (on b112 b72)
    (on b72 b103)
    (on b103 b173)
    (on b173 b195)
    (on-table b195)
    (clear b207)
    (on b207 b184)
    (on b184 b135)
    (on b135 b125)
    (on b125 b240)
    (on b240 b225)
    (on-table b225)
    (clear b78)
    (on b78 b196)
    (on b196 b27)
    (on-table b27))
 (:goal  (and 
    (clear b150)
    (on b150 b213)
    (on b213 b7)
    (on b7 b132)
    (on-table b132)
    (clear b185)
    (on b185 b141)
    (on b141 b166)
    (on b166 b205)
    (on b205 b114)
    (on b114 b55)
    (on b55 b65)
    (on-table b65)
    (clear b87)
    (on b87 b6)
    (on-table b6)
    (clear b23)
    (on b23 b28)
    (on b28 b133)
    (on b133 b70)
    (on b70 b240)
    (on b240 b29)
    (on b29 b17)
    (on b17 b250)
    (on b250 b156)
    (on b156 b109)
    (on b109 b181)
    (on-table b181)
    (clear b178)
    (on b178 b119)
    (on b119 b31)
    (on b31 b47)
    (on b47 b234)
    (on-table b234)
    (clear b50)
    (on b50 b105)
    (on b105 b248)
    (on b248 b72)
    (on b72 b175)
    (on b175 b52)
    (on b52 b118)
    (on b118 b24)
    (on b24 b67)
    (on b67 b76)
    (on b76 b192)
    (on-table b192)
    (clear b13)
    (on b13 b194)
    (on b194 b25)
    (on b25 b174)
    (on b174 b144)
    (on-table b144)
    (clear b121)
    (on b121 b135)
    (on b135 b71)
    (on b71 b127)
    (on b127 b2)
    (on b2 b211)
    (on b211 b16)
    (on b16 b139)
    (on b139 b177)
    (on-table b177)
    (clear b188)
    (on b188 b216)
    (on b216 b38)
    (on b38 b94)
    (on b94 b102)
    (on b102 b41)
    (on b41 b110)
    (on b110 b203)
    (on b203 b117)
    (on b117 b190)
    (on b190 b116)
    (on b116 b198)
    (on b198 b125)
    (on b125 b73)
    (on b73 b136)
    (on b136 b101)
    (on-table b101)
    (clear b111)
    (on b111 b32)
    (on b32 b249)
    (on b249 b207)
    (on b207 b98)
    (on b98 b233)
    (on b233 b159)
    (on b159 b162)
    (on b162 b146)
    (on b146 b58)
    (on b58 b220)
    (on b220 b201)
    (on b201 b210)
    (on b210 b81)
    (on-table b81)
    (clear b236)
    (on b236 b107)
    (on b107 b8)
    (on b8 b182)
    (on b182 b95)
    (on b95 b129)
    (on b129 b90)
    (on b90 b176)
    (on b176 b246)
    (on b246 b204)
    (on b204 b237)
    (on b237 b158)
    (on-table b158)
    (clear b191)
    (on b191 b51)
    (on b51 b79)
    (on b79 b3)
    (on b3 b66)
    (on b66 b14)
    (on-table b14)
    (clear b89)
    (on b89 b193)
    (on b193 b134)
    (on b134 b218)
    (on b218 b126)
    (on b126 b230)
    (on b230 b44)
    (on-table b44)
    (clear b202)
    (on b202 b77)
    (on b77 b224)
    (on b224 b1)
    (on b1 b15)
    (on b15 b11)
    (on b11 b171)
    (on b171 b85)
    (on-table b85)
    (clear b247)
    (on b247 b60)
    (on b60 b26)
    (on b26 b39)
    (on b39 b231)
    (on b231 b93)
    (on b93 b124)
    (on b124 b4)
    (on b4 b143)
    (on b143 b153)
    (on b153 b206)
    (on b206 b221)
    (on b221 b99)
    (on b99 b232)
    (on b232 b18)
    (on b18 b155)
    (on b155 b244)
    (on b244 b241)
    (on b241 b19)
    (on b19 b88)
    (on b88 b61)
    (on b61 b228)
    (on b228 b223)
    (on b223 b75)
    (on-table b75)
    (clear b80)
    (on b80 b5)
    (on b5 b145)
    (on b145 b113)
    (on b113 b189)
    (on b189 b40)
    (on b40 b209)
    (on b209 b62)
    (on b62 b147)
    (on b147 b46)
    (on b46 b131)
    (on b131 b27)
    (on b27 b208)
    (on b208 b37)
    (on b37 b112)
    (on b112 b170)
    (on b170 b195)
    (on b195 b122)
    (on b122 b172)
    (on b172 b49)
    (on b49 b69)
    (on b69 b227)
    (on-table b227)
    (clear b78)
    (on b78 b91)
    (on b91 b34)
    (on b34 b222)
    (on-table b222)
    (clear b187)
    (on b187 b96)
    (on b96 b33)
    (on b33 b82)
    (on b82 b157)
    (on b157 b103)
    (on-table b103)
    (clear b53)
    (on b53 b180)
    (on b180 b97)
    (on b97 b56)
    (on b56 b20)
    (on-table b20)
    (clear b186)
    (on b186 b92)
    (on b92 b239)
    (on b239 b148)
    (on b148 b212)
    (on b212 b21)
    (on b21 b183)
    (on b183 b63)
    (on b63 b168)
    (on b168 b59)
    (on b59 b22)
    (on b22 b9)
    (on b9 b242)
    (on b242 b217)
    (on b217 b169)
    (on b169 b57)
    (on-table b57)
    (clear b160)
    (on b160 b149)
    (on b149 b10)
    (on b10 b120)
    (on b120 b214)
    (on b214 b154)
    (on b154 b229)
    (on b229 b245)
    (on b245 b64)
    (on b64 b83)
    (on b83 b184)
    (on-table b184)
    (clear b100)
    (on b100 b86)
    (on b86 b104)
    (on b104 b137)
    (on b137 b152)
    (on b152 b12)
    (on b12 b179)
    (on b179 b138)
    (on b138 b225)
    (on-table b225)
    (clear b243)
    (on b243 b197)
    (on b197 b151)
    (on b151 b115)
    (on b115 b35)
    (on b35 b130)
    (on b130 b54)
    (on b54 b140)
    (on b140 b84)
    (on b84 b161)
    (on b161 b219)
    (on b219 b128)
    (on b128 b200)
    (on b200 b106)
    (on b106 b199)
    (on b199 b163)
    (on b163 b226)
    (on b226 b36)
    (on b36 b74)
    (on b74 b165)
    (on b165 b238)
    (on b238 b167)
    (on b167 b164)
    (on b164 b42)
    (on b42 b108)
    (on b108 b68)
    (on b68 b215)
    (on b215 b235)
    (on b235 b142)
    (on b142 b196)
    (on b196 b48)
    (on b48 b43)
    (on-table b43)
    (clear b30)
    (on b30 b45)
    (on b45 b173)
    (on b173 b123)
    (on-table b123))))